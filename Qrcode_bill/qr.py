import qrcode
import json 

data= json.dumps({
    "invoice": "12",
    "amount": "160",
    "customer": "John"
})
qr = qrcode.QRCode(
    version=3,  # or higher for more data
    error_correction=qrcode.constants.ERROR_CORRECT_Q,
    box_size=10,
    border=4,
)
qr.add_data(data)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save("Qrcode_bill\qr_imgs\qrimg.png")