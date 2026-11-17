from app.models.extras import AdminSession, AdminUser, AuthSession, EmailVerificationToken, Notification, PasswordResetToken
from app.models.generated import GENERATED_MODELS

for _model in GENERATED_MODELS.values():
    globals()[_model.__name__] = _model

__all__ = sorted(model.__name__ for model in GENERATED_MODELS.values()) + [
    "AdminSession",
    "AdminUser",
    "AuthSession",
    "EmailVerificationToken",
    "Notification",
    "PasswordResetToken",
]
