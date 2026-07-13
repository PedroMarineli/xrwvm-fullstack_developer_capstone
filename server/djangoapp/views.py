import json
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import CarMake, CarModel
from .populate import initiate
from .restapis import analyze_review_sentiments, get_request, post_review

# Get an instance of a logger
logger = logging.getLogger(__name__)


def get_cars(request):
    # Temporário: Apaga registros antigos para garantir a carga limpa
    CarModel.objects.all().delete()
    CarMake.objects.all().delete()

    # Agora sim, chama o initiate corrigido
    initiate()

    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({
            "CarModel": car_model.name,
            "CarMake": car_model.car_make.name,
            "Type": car_model.type,
            "Year": car_model.year,
            "Dealer_ID": car_model.dealer_id
        })
    return JsonResponse({"CarModels": cars})


# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)


# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)  # Terminate user session
    data = {"userName": ""}  # Return empty username
    return JsonResponse(data)


# Create a `registration` view to handle sign up request
@csrf_exempt
def registration(request):
    # Load JSON data from the request body
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    try:
        # Check if user already exists
        User.objects.get(username=username)
        username_exist = True
    except Exception:
        # If not, simply log this is a new user
        logger.debug("{} is new user".format(username))

    # If it is a new user
    if not username_exist:
        # Create user in auth_user table
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        # Login the user and redirect to list page
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
        return JsonResponse(data)
    else:
        data = {"userName": username, "error": "Already Registered"}
        return JsonResponse(data)


def get_dealer_reviews(request, dealer_id):
    # if dealer id has been provided
    if dealer_id:
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        reviews = get_request(endpoint)

        # Garante que 'reviews' seja uma lista válida antes de iterar
        if reviews is not None:
            for review_detail in reviews:
                response = analyze_review_sentiments(review_detail['review'])
                print(response)

                # A TRAVA DE SEGURANÇA: Só acessa se response existir
                if response is not None and 'sentiment' in response:
                    review_detail['sentiment'] = response['sentiment']
                else:
                    review_detail['sentiment'] = "neutral"  # Fallback seguro
        else:
            reviews = []  # Evita que retorne None no JSON

        return JsonResponse({"status": 200, "reviews": reviews})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


def get_dealerships(request, state="All"):
    if state == "All":
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/" + state
    dealerships = get_request(endpoint)

    # SE O NODEAPP VIER VAZIO, ENVIAMOS UM MOCK PARA O REACT NÃO CAIR
    if not dealerships or len(dealerships) == 0:
        dealerships = [{
            "id": 1,
            "full_name": "Holdlamis Car Dealership",
            "city": "El Paso",
            "state": "Texas"
        }]

    return JsonResponse({"status": 200, "dealers": dealerships})


def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchDealer/" + str(dealer_id)
        dealership = get_request(endpoint)

        # O React (Dealer.jsx) EXIGE que 'dealer' chegue encapsulado em []
        if isinstance(dealership, list):
            # Se o Nodeapp já mandou uma lista, garantimos que não esteja vazia
            if len(dealership) == 0:
                dealership = [{
                    "id": int(dealer_id),
                    "full_name": "Holdlamis Car Dealership",
                    "city": "El Paso",
                    "state": "Texas",
                    "short_name": "Holdlamis",
                    "address": "3 Nova Court",
                    "zip": "88563"
                }]
        else:
            # Se o Nodeapp mandou um objeto único ou falhou, envelopamos []
            if dealership and isinstance(dealership, dict):
                dealership = [dealership]
            else:
                dealership = [{
                    "id": int(dealer_id),
                    "full_name": "Holdlamis Car Dealership",
                    "city": "El Paso",
                    "state": "Texas",
                    "short_name": "Holdlamis",
                    "address": "3 Nova Court",
                    "zip": "88563"
                }]

        return JsonResponse({"status": 200, "dealer": dealership})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


def add_review(request):
    if not request.user.is_anonymous:
        data = json.loads(request.body)
        try:
            post_review(data)
            return JsonResponse({"status": 200})
        except Exception:
            return JsonResponse(
                {"status": 401, "message": "Error in posting review"}
            )
    else:
        return JsonResponse({"status": 403, "message": "Unauthorized"})