COUNTRY_CODE_CHOICES = [
    ('502', '+502 Guatemala'),
    ('503', '+503 El Salvador'),
    ('504', '+504 Honduras'),
    ('505', '+505 Nicaragua'),
    ('506', '+506 Costa Rica'),
    ('507', '+507 Panamá'),
    ('501', '+501 Belice'),
    ('52', '+52 México'),
    ('1', '+1 Estados Unidos / Canadá'),
    ('57', '+57 Colombia'),
    ('51', '+51 Perú'),
    ('56', '+56 Chile'),
    ('54', '+54 Argentina'),
    ('55', '+55 Brasil'),
    ('34', '+34 España'),
]

DEFAULT_COUNTRY_CODE = '502'

# Longitud máxima del número local (sin código de país).
COUNTRY_PHONE_LENGTHS = {
    '502': 8,
    '503': 8,
    '504': 8,
    '505': 8,
    '506': 8,
    '507': 8,
    '501': 7,
    '52': 10,
    '1': 10,
    '57': 10,
    '51': 9,
    '56': 9,
    '54': 10,
    '55': 11,
    '34': 9,
}

DEFAULT_PHONE_LENGTH = 10
