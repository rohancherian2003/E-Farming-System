from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from .firebase_config import db
import random
import os

class MockImage:
    def __init__(self, name):
        self.url = f'/media/{name}' if name else ''

class ObjWrapper:
    def __init__(self, d, doc_id=None):
        for k, v in d.items():
            setattr(self, k, v)
        if doc_id:
            self.id = doc_id
        if 'image' in d and d['image']:
            self.image = MockImage(d['image'])
        elif 'image' not in d:
            self.image = MockImage('')

def get_all(collection):
    if not db: return []
    return [ObjWrapper(doc.to_dict(), doc.id) for doc in db.collection(collection).stream()]

def get_where(collection, field, op, value):
    if not db: return []
    return [ObjWrapper(doc.to_dict(), doc.id) for doc in db.collection(collection).where(field, op, value).stream()]

def get_by_id(collection, doc_id):
    if not db: return []
    doc = db.collection(collection).document(doc_id).get()
    if doc.exists:
        return [ObjWrapper(doc.to_dict(), doc.id)]
    return []

def add_doc(collection, data):
    if not db: return None
    _, ref = db.collection(collection).add(data)
    return ref.id

def update_doc(collection, doc_id, data):
    if not db: return
    db.collection(collection).document(doc_id).update(data)

def delete_doc(collection, doc_id):
    if not db: return
    db.collection(collection).document(doc_id).delete()

# --- Views ---

def index(request):
    prd = get_all('Products')
    return render(request, "index.html", {'prd': prd})

def signIn(request):
    msg = ''
    if request.method == "POST":
        email = request.POST.get('email')
        pword = request.POST.get('pword')
        log = get_where('Registration', 'email', '==', email)
        log = [l for l in log if l.password == pword]
        if log:
            for i in log:
                rights = i.rights
                if rights == "User":
                    request.session['email'] = email
                    return redirect("/user/")
                elif rights == "Farmer":
                    request.session['email'] = email
                    request.session['name'] = i.name
                    return redirect('/farmer/')
                elif rights == 'Admin':
                    request.session['name'] = i.name
                    return redirect("/adminp/")
                else:
                    msg = 'Falied'
        else:
            msg = 'Falied'
    return render(request, "sign.html", {'msg': msg})

def signUp(request):
    sub = ''
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        pword = request.POST.get('pword')
        add_doc('Registration', {'name': name, 'email': email, 'password': pword, 'rights': 'User'})
        sub = 'Success'
    return render(request, "sign.html", {'sub': sub})

def farmer_reg(request):
    sub = ''
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        pword = request.POST.get('pword')
        add_doc('Registration', {'name': name, 'email': email, 'password': pword, 'rights': 'New Farmer'})
        sub = 'Success'
    return render(request, "farmer_reg.html", {'sub': sub})

def user(request):
    prd = get_all('Products')
    return render(request, "buyer/user.html", {'prd': prd})

def admin(request):
    name = request.session.get('name', '')
    reg = get_where('Registration', 'rights', '==', 'User')
    return render(request, "admin/admin.html", {'name': name, 'reg': reg})

def farmers(request):
    reg = get_where('Registration', 'rights', '==', 'Farmer')
    if request.method == "POST":
        search = request.POST.get('search')
        if search:
            reg = get_where('Registration', 'email', '==', search)
    return render(request, "admin/farmers.html", {'reg': reg})

def users(request):
    reg = get_where('Registration', 'rights', '==', 'User')
    if request.method == "POST":
        search = request.POST.get('search')
        if search:
            reg = get_where('Registration', 'email', '==', search)
    return render(request, "admin/users.html", {'reg': reg})

def farmer(request):
    email = request.session.get('email')
    name = request.session.get('name')
    ord_info = []
    revenue = 0
    inventory = 0
    torders = 0
    processed_order_ids = set() 
    
    if db:
        orders = []
        for d in db.collection('Orders').where('status', 'in', ['Pending', 'Shipped']).stream():
            orders.append(ObjWrapper(d.to_dict(), d.id))
    else:
        orders = []

    pro = get_where('Products', 'farmer', '==', email)
    for i in pro:
        inventory += int(i.price)
        
    for order in orders:
        if order.order_id not in processed_order_ids:
            processed_order_ids.add(order.order_id)
            torders = len(processed_order_ids)
            pid = order.product
            pp = get_by_id('Products', pid)
            pp = [p for p in pp if p.farmer == email]
            for product in pp:
                revenue += int(product.price) * int(order.quantity) 
                ord_info.append({'orders': order, 'products': product})
    return render(request, "seller/farmer.html", {'name': name, 'ord_info': ord_info, 'revenue': revenue, 'inventory': inventory, 'torders': torders}) 

def new_farmers(request):
    frm = get_where('Registration', 'rights', '==', 'New Farmer')
    return render(request, "admin/new_farmers.html", {'frm': frm})

def app_frm(request, id):
    update_doc('Registration', id, {'rights': 'Farmer'})
    return redirect('/new_farmers/')

def rej_frm(request, id):
    update_doc('Registration', id, {'rights': 'Rejected'})
    return redirect('/new_farmers/')

def add_product(request):
    name = request.session.get('name')
    email = request.session.get('email')
    msg = ''
    prmsg = ''
    qnmsg = ''
    sub = ''
    if request.method == "POST":
        image = request.FILES.get('image')
        pname = request.POST.get('pname')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        desc = request.POST.get('desc')
        if pname.isnumeric():
            msg = "Invalid Product Name"
        if not price.isnumeric():
            prmsg = "Invalid Price"
        if not quantity.isnumeric():
            qnmsg = "Invalid Quantity"
        else:
            filename = ''
            if image:
                fs = FileSystemStorage(location='media/images/')
                filename = fs.save(image.name, image)
                filename = 'images/' + filename

            add_doc('Products', {
                'image': filename,
                'farmer': email,
                'pname': pname,
                'price': int(price),
                'quantity': int(quantity),
                'description': desc
            })
            sub = 'Success'
    return render(request, "seller/add_product.html", {'name': name, 'msg': msg, 'prmsg': prmsg, 'qnmsg': qnmsg, 'sub': sub})

def view_products(request):
    name = request.session.get('name')
    email = request.session.get('email')
    prd = get_where('Products', 'farmer', '==', email)
    if request.method == "POST":
        search = request.POST.get('search')
        if search:
            prd = get_by_id('Products', search)
    return render(request, "seller/view_products.html", {'prd': prd, 'name': name})

def del_prod(request, id):
    delete_doc('Products', id)
    return redirect('/view_products/')

def edit_product(request, id):
    prd = get_by_id('Products', id)
    name = request.session.get('name')
    sub = ''
    if request.method == "POST":
        pname = request.POST.get('pname')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        desc = request.POST.get('desc')
        update_doc('Products', id, {
            'pname': pname,
            'price': int(price),
            'quantity': int(quantity),
            'description': desc
        })
        sub = 'Success'
        prd = get_by_id('Products', id)
    return render(request, "seller/edit_product.html", {'prd': prd, 'name': name, 'sub': sub})

def products(request):
    prd = get_all('Products')
    return render(request, "buyer/products.html", {'prd': prd})

def product_detail(request, id):
    prd = get_by_id('Products', id)
    return render(request, "buyer/product-detail.html", {'prd': prd})

def add_cart(request, id):
    user = request.session.get('email')
    add_doc('Cart', {'user': user, 'product': id, 'quantity': 1})
    return redirect(request.META.get('HTTP_REFERER', '/'))

def remove_cart(request, id):
    delete_doc('Cart', id)
    return redirect(request.META.get('HTTP_REFERER', '/'))

def cart(request):
    email = request.session.get('email')
    cart_items = get_where('Cart', 'user', '==', email)
    prd = []
    sub_total = 0
    for i in cart_items:
        cid = i.id
        product_id = i.product
        quan = int(i.quantity)
        prds = get_by_id('Products', product_id)
        for j in prds:
            price = int(j.price)
            total = quan * price
            sub_total += total
            prd.append({'products': j, 'quantity': quan, 'total': total, 'cid': cid})

    if request.method == "POST":
        if 'update' in request.POST:
            products_list = request.POST.getlist('product')
            for pro in products_list:
                quantity = request.POST.get(f'quantity_{pro}')
                if quantity is not None and quantity.isdigit():
                    c_items = get_where('Cart', 'product', '==', pro)
                    for c in c_items:
                        if c.user == email:
                            update_doc('Cart', c.id, {'quantity': int(quantity)})
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return render(request, 'buyer/cart.html', {'prd': prd, 'sub_total': sub_total})

def checkout(request):
    email = request.session.get('email')
    cart_items = get_where('Cart', 'user', '==', email)
    prd = []
    sub_total = 0
    for i in cart_items:
        product_id = i.product
        quan = int(i.quantity)
        prds = get_by_id('Products', product_id)
        for j in prds:
            price = int(j.price)
            total = quan * price
            sub_total += total
            prd.append({'products': j, 'quantity': quan, 'total': total})
            
    if request.method == "POST":
        oid = random.randint(10000, 99999)
        fname = request.POST.get('fname')
        em = request.POST.get('email')
        address = request.POST.get('address')
        country = request.POST.get('country')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip')
        cname = request.POST.get('cname')
        cno = request.POST.get('cno')
        exp = request.POST.get('exp')
        cvv = request.POST.get('cvv')
        
        for k in cart_items:
            product_id = k.product
            quant = int(k.quantity)
            prds = get_by_id('Products', product_id)
            for l in prds:
                q = int(l.quantity)
                add_doc('Orders', {'order_id': oid, 'user': email, 'product': product_id, 'quantity': quant, 'status': 'Pending'})
                update_doc('Products', product_id, {'quantity': q - quant})
                
        add_doc('Address', {'order': oid, 'name': fname, 'email': em, 'address': address, 'country': country, 'state': state, 'zip': zip_code})
        add_doc('Payment', {'order': oid, 'name_card': cname, 'cno': cno, 'cdate': exp, 'cvv': cvv})
        
        for k in cart_items:
            delete_doc('Cart', k.id)
            
        return redirect('/order_placed/')
    return render(request, 'buyer/checkout.html', {'prd': prd, 'sub_total': sub_total})

def order_placed(request):
    return render(request, 'buyer/order_placed.html')

def orders(request):
    email = request.session.get('email')
    orders_list = []
    ord_items = get_where('Orders', 'user', '==', email)
    for i in ord_items:
        product_id = i.product
        prd = get_by_id('Products', product_id)
        for j in prd:
            orders_list.append({'products': j, 'ord': i})
    return render(request, 'buyer/orders.html', {'orders': orders_list})

def new_orders(request):
    email = request.session.get('email')
    name = request.session.get('name')
    ord_info = []
    processed_order_ids = set()
    
    if db:
        orders_items = []
        for d in db.collection('Orders').where('status', 'in', ['Pending', 'Shipped']).stream():
            orders_items.append(ObjWrapper(d.to_dict(), d.id))
    else:
        orders_items = []
        
    if request.method == "POST":
        search = request.POST.get('search', '').strip()
        if search:
            orders_items = [o for o in orders_items if str(o.order_id) == search]
            
    for order in orders_items:
        if order.order_id not in processed_order_ids:
            processed_order_ids.add(order.order_id)
            pid = order.product
            pp = get_by_id('Products', pid)
            pp = [p for p in pp if p.farmer == email]
            for product in pp:
                ord_info.append({'orders': order, 'products': product})
                
    return render(request, 'seller/new_orders.html', {'ord_info': ord_info, 'name': name})

def view_orders_products(request, oid):
    ord_items = get_where('Orders', 'order_id', '==', int(oid))
    if not ord_items:
        ord_items = get_where('Orders', 'order_id', '==', str(oid))
        
    name = request.session.get('name')
    pname = ''
    address = ''
    
    for i in ord_items:
        pid = i.product
        prd = get_by_id('Products', pid)
        for j in prd:
            pname = j.pname
        add_items = get_where('Address', 'order', '==', int(oid))
        if not add_items:
            add_items = get_where('Address', 'order', '==', str(oid))
        for k in add_items:
            address = k.address
            
    return render(request, 'seller/view_orders_products.html', {'ord': ord_items, 'pname': pname, 'address': address, 'name': name})

def ship_product(request, oid):
    ord_items = get_where('Orders', 'order_id', '==', int(oid))
    if not ord_items:
        ord_items = get_where('Orders', 'order_id', '==', str(oid))
    for i in ord_items:
        update_doc('Orders', i.id, {'status': 'Shipped'})
    return redirect(request.META.get('HTTP_REFERER', '/'))

def cancel_order(request, id):
    update_doc('Orders', id, {'status': 'Cancel Requested'})
    return redirect(request.META.get('HTTP_REFERER', '/'))

def cancel_requests(request):
    email = request.session.get('email')
    name = request.session.get('name')
    prd = get_where('Products', 'farmer', '==', email)
    orders_list = []
    for i in prd:
        pid = i.id
        ord_items = get_where('Orders', 'product', '==', pid)
        ord_items = [o for o in ord_items if o.status == 'Cancel Requested']
        for j in ord_items:
            orders_list.append({'orders': j})
    return render(request, "seller/cancel_requests.html", {'orders': orders_list, 'name': name})

def accept_cancel(request, id):
    update_doc('Orders', id, {'status': 'Canceled'})
    return redirect(request.META.get('HTTP_REFERER', '/'))

def profile(request):
    email = request.session.get('email')
    reg = get_where('Registration', 'email', '==', email)
    msg = ''
    sub = ''
    if request.method == "POST":
        name = request.POST.get('name')
        pword = request.POST.get('pword')
        if name.isnumeric():
            msg = 'Invalid Name'
        else:
            for r in reg:
                update_doc('Registration', r.id, {'name': name, 'password': pword})
            sub = 'Success'
            reg = get_where('Registration', 'email', '==', email)
    return render(request, "buyer/profile.html", {'reg': reg, 'msg': msg, 'sub': sub})