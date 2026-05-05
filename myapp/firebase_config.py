import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase Admin SDK
# You need to download your serviceAccountKey.json from Firebase Console
# and place it in the same directory as this file.

cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')

if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    print("WARNING: serviceAccountKey.json not found! Firebase will not work.")
    db = None
