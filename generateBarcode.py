import qrcode

# Data for NIM and Nama
nim = "A11.2021"
nama = "Lutfia Arum Naflasari"

# Combine NIM and Nama into a single string
data = f"NIM: {nim}, Nama: {nama}"

# Generate the QR code
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(data)
qr.make(fit=True)

# Create an image from the QR code
qr_image = qr.make_image(fill_color="black", back_color="white")

# Save the QR code image
qr_image.save("qrcode.png")
