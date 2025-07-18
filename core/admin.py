from django.contrib import admin
from .models import CustomUser, SleepRecord, SportRecord, FoodItem, Meal, MealItem

admin.site.register(CustomUser)
admin.site.register(SleepRecord)
admin.site.register(SportRecord)
admin.site.register(FoodItem)
admin.site.register(Meal)
admin.site.register(MealItem)
