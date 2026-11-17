from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone_number")
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "phone_number",
        )

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
