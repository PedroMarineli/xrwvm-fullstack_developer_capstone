from django.db import models
from django.utils.timezone import now
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.

# Car Make Model
class CarMake(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    # Você pode adicionar outros campos aqui se desejar (ex: country)

    def __str__(self):
        return self.name


# Car Model Model
class CarModel(models.Model):
    car_make = models.ForeignKey(CarMake, on_delete=models.CASCADE)  # Many-to-One relationship
    name = models.CharField(max_length=100)
    
    # Campo para o ID do Dealer (referência ao banco Cloudant)
    dealer_id = models.IntegerField()

    CAR_TYPES = [
        ('SEDAN', 'Sedan'),
        ('SUV', 'SUV'),
        ('WAGON', 'Wagon'),
        ('COUPE', 'Coupe'),
        ('HATCHBACK', 'Hatchback')
    ]
    type = models.CharField(max_length=10, choices=CAR_TYPES, default='SUV')
    
    # Ano com validação entre 2015 e 2023 conforme as instruções do lab
    year = models.IntegerField(
        default=2023,
        validators=[
            MaxValueValidator(2023),
            MinValueValidator(2015)
        ]
    )

    def __str__(self):
        return f"{self.car_make.name} {self.name}"  # Retorna Make + Model para melhor identificação