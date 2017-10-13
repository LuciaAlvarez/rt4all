import matplotlib.pyplot as plt
import numpy as np
import time
import os
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas



def graphic(variableGrafica, dataArray, initTime, interval):
	
		#generate timeArray 
		timeArray = []
		for i in range(len(dataArray)):
			timeArray.append(initTime + interval*i)
		print timeArray

		#plot
   		plt.xlabel('time')
		plt.ylabel(variableGrafica + ' samples')
		plt.title(variableGrafica)
		plt.grid(True)
		plt.plot(timeArray, dataArray, 'ro', timeArray, dataArray, 'g')
		plt.savefig('/var/tmp/'+variableGrafica+'.png')
		#plt.show()

		
		

		

def createPDF(user, machine, id, ip):


		#generate a PDF
		aux = canvas.Canvas("./pdf/LAG.pdf")
		aux.drawImage("./logo.png",400, 750, 200,100)
		aux.drawString(50,800,'****REPORT FILE****')
		aux.drawString(50,750,'Date: '+ time.strftime("%d/%m/%y"))
		aux.drawString(50,730,'Report time: ' +time.strftime("%H:%M:%S"))
		aux.drawString(50,710,'Worker: ' +user)
		aux.drawString(50,690,'Machine: ' +machine + '      ID: ' +id+'      IP: ' +ip)
	
		#aux.drawString(150,20,"Posicion (X,Y) = (150,20)")


		aux.drawString(50,50,"RT4ALL logger")
		#include graphics

		aux.drawImage("/var/tmp/Temperature.png",100 , 350, 400,250)
		aux.drawImage("/var/tmp/Humidity.png",100, 80,400,250)
		

		aux.showPage()
		aux.save()

	


if __name__ == "__main__":

	#variableGrafica = input()
	dataArray = [23,54,36,78, 32,76,12, 23,54,36,78, 32,76,12]
	graphic('Temperature',dataArray, 1, 0.5)
	graphic('Humidity',dataArray, 1, 0.5)
	createPDF('Lucia', 'robot1', 'id1', '192.168.1.1');
	
	
	





