from gpiozero import LED
from time import sleep

# This drives your MOSFET gate
valve = LED(17)

print("Solenoid test starting")

# Make sure it starts off
valve.off()
sleep(1)

# Turn it on for two seconds
print("Valve ON")
valve.on()
sleep(30)

# Turn it off
print("Valve OFF")
valve.off()
sleep(1)

print("Test complete")
