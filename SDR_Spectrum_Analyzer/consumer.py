#!/usr/bin/python
# -*- coding: utf-8 -*-
from json import dumps
import requests

# Send data to web service, passing a JSON object as INPUT
def send_json(payload, url = 'http://radiogis.uis.edu.co/sensores/medidas', type = 'json'):

  if type == 'json':
    headers = {'content-type': 'application/json'}
  elif type == 'xml':
    headers = {'content-type': 'application/xml'}
  else:
    print("unknown content type")
    return -1

  r = requests.post(url, data=dumps(payload), headers=headers)

  print(r)
  return 1

# Send data to web service, passing each value (one by one)
# date = String with any valid date format.
# tag = Any aditional information that you consider necessary, such as band.
# value = A number (for single sensors) or a matrix stored in a string (using semicolons for rows and tabs for columns).
# sensor_id = valid ids, as of 03.06.15 numbers from 1 to 3, to add other sensors go to: http://radiogis.uis.edu.co/sensores/web/sensor.
# type_id = 1, 2 or 3, as of 05.04.15 this is a dummy column (it probably makes no sense).
# comment = Optional, any string-like text you want to pass.
# latitude = numeric value or string containning a numeric value
# longitude = numeric value or string containning a numeric value

def send_raw(date, tag, value, sensor_id, type_id, longitude, latitude, campaign,
    comment = None, url = 'http://radiogis.uis.edu.co/sensores/medidas', 
    type = 'json'): 

  payload = {"fecha_toma": date, "etiqueta": tag, "valor_medido": value,
   "sensor": sensor_id, "tipo": type_id, "comentario": comment,
   "latitud": latitude, "longitud": longitude, "campanya":campaign}
  send_json(payload, url, type)
  return 1
