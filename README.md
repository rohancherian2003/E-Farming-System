# E-Farming System

This is a comprehensive E-commerce and agricultural management web application built with **Django** and html,CSS,Javasript,**Firebase Firestore**. The platform connects farmers directly with buyers, allowing farmers to list their agricultural products and buyers to purchase them securely.

## Features
- **3 User Roles**: Admin, Farmer (Seller), and User (Buyer).
- **Firebase Firestore Integration**: Uses NoSQL collections for efficient and real-time data storage.
- **Order Management**: Cart system, secure checkout flow, and order status tracking.
- **Admin Dashboard**: Approve or reject new farmer registrations.

---

## 🚀 How to Run the Project (Step-by-Step)

Follow these instructions to run the project locally on your machine.

### Prerequisites
Make sure you have the following installed:
- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- A Firebase Account (for setting up your own Firestore Database)

### 1. Clone the Repository
Open your terminal and clone the repository:
```bash
git clone https://github.com/rohancherian2003/E-Farming-System.git
cd E-Farming-System
```

### 2. Create a Virtual Environment (Optional but Recommended)
It is best practice to create a virtual environment to manage dependencies:
```bash
python -m venv venv
```
Activate the virtual environment:
- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

### 3. Install Dependencies
Install all the required Python packages using `pip`:
```bash
pip install -r requirements.txt
```

### 4. Setup Firebase Credentials
Because this project uses Firebase Firestore, you need to provide your own service account key.
1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Create a new project (or select an existing one).
3. Go to **Build > Firestore Database** and click **Create database** (Start in Test Mode).
4. Go to **Project Settings** (the gear icon) > **Service Accounts**.
5. Click **Generate new private key**. This will download a `.json` file to your computer.
6. Rename this downloaded file to exactly **`serviceAccountKey.json`**.
7. Move `serviceAccountKey.json` into the `myapp/` folder of this project.

*Note: The `serviceAccountKey.json` is highly sensitive and is ignored in `.gitignore` so it will not be pushed to GitHub.*

### 5. Run the Server
Once your database is configured and your dependencies are installed, you can start the Django development server:

```bash
python manage.py runserver
```

Open your browser and navigate to:
**[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

