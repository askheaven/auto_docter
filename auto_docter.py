#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import cv2
import numpy as np
import time
import uiautomator2 as u2
import matplotlib.pyplot as plt
import subprocess
import os

from ctypes import *

START = 1
START2 = 2
ENERGY = 3
END = 4
RUN = 5
STONE_ENERGY = 6

IMG = (START, START2, ENERGY, END, RUN, STONE_ENERGY)

class AutoDocter():

	def __init__(self):
		self.img = {}
		self.device = None
		self.status = 0

		self.times = 0
		self.use_item = {"stone":0, "energy":0}

	def init_config(self):
		with open("./config.ini", "r", encoding="utf8") as f:
			for line in f.readlines():
				if line.startswith("#"):
					continue
				config = line.strip("\n").split("=")
				setattr(self, config[0], int(config[1]))
		self.ip_address = "127.0.0.1:" + str(self.port)

	def init_device(self):
		try:
			self.device = u2.connect(self.ip_address)
		except Exception:
			self.device = u2.connect(self.ip_address)
			# print("init_device_error", Exception)

	def init_img(self):
		for img in IMG:
			self.img[img] = {}
		self.img[START]["img"] = cv2.imread(r'.\img\start.png')
		self.img[START]["size"] = self.img[START]["img"].shape[:2]

		self.img[START2]["img"] = cv2.imread(r'.\img\start2.png')
		self.img[START2]["size"] = self.img[START2]["img"].shape[:2]

		self.img[ENERGY]["img"] = cv2.imread(r'.\img\energy.png')
		self.img[ENERGY]["size"] = self.img[ENERGY]["img"].shape[:2]

		self.img[END]["img"] = cv2.imread(r'.\img\end.png')
		self.img[END]["size"] = self.img[END]["img"].shape[:2]

		self.img[STONE_ENERGY]["img"] = cv2.imread(r'.\img\stone_energy.png')
		self.img[STONE_ENERGY]["size"] = self.img[STONE_ENERGY]["img"].shape[:2]

		self.img[RUN]["img"] = cv2.imread(r'.\img\run.png')
		self.img[RUN]["size"] = self.img[RUN]["img"].shape[:2]

	def init_adb_connect(self):
		os.system(r'.\adb\adb.exe kill-server ')
		os.system(r'.\adb\adb.exe start-server ')
		os.system(r'.\adb\adb.exe connect '+self.ip_address)

	def click(self,x, y):
		time.sleep(1)
		self.device.click(x,y)

	#找图 返回最近似的点
	def search_returnPoint(self,img,flag):
		template = self.img[flag]["img"]
		template_size = self.img[flag]["size"]
		img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		template_ = cv2.cvtColor(template,cv2.COLOR_BGR2GRAY)
		result = cv2.matchTemplate(img_gray, template_,cv2.TM_CCOEFF_NORMED)
		threshold = 0.8
		# res大于80%
		loc = np.where(result >= threshold)

		# 使用灰度图像中的坐标对原始RGB图像进行标记
		point = ()
		for pt in zip(*loc[::-1]):
			cv2.rectangle(img, pt, (pt[0] + template_size[1], pt[1] + + template_size[0]), (7, 249, 151), 2)
			point = pt
		if point==():
			return None,None,None
		return img, point[0]+ template_size[1] /2,float(point[1])

	def run_loop(self):
		self.device.screenshot(r".\img\screenshot.png")
		img_screen = cv2.imread(r'.\img\screenshot.png')
		if self.status == 0:
			res_start, x, y = self.search_returnPoint(img_screen, START)
			if res_start is not None:
				self.click(x,y)
				self.status += 1

		elif self.status == 1:
			res_start2, x1, y1 = self.search_returnPoint(img_screen, START2)
			res_energy, x2, y2 = self.search_returnPoint(img_screen, ENERGY)
			res_stone, x3, y3 = self.search_returnPoint(img_screen, STONE_ENERGY)
			if res_start2 is not None:
				self.click(x1,y1)
				self.status += 1
			elif res_stone is not None:
				if self.use_stone:
					self.click(x2,y2)
					self.status -= 1
					self.use_stone -= 1
					self.use_item["stone"] += 1
					print("use stone")
				else:
					return "stone_energy_out, {}".format(self.use_stone)
			elif res_energy is not None:
				if self.use_energy:
					self.click(x2,y2)
					self.status -= 1
					self.use_item["energy"] += 1
					print("use energy")
				else:
					return "energy_out"
			
		elif self.status == 2 is not None:
			res_end, x, y = self.search_returnPoint(img_screen, END)
			if res_end is not None:
				time.sleep(2)
				self.click(x,y)
				self.status = 0
				self.limit_times -= 1
				self.times += 1
				print(self.times)
			else:
				time.sleep(5)

	def start(self):
		self.init_config()
		self.init_adb_connect()
		self.init_device()
		self.init_img()
		
		res = ""
		while self.limit_times and not res:
			res = self.run_loop()
			time.sleep(1)
		print(res)
		print(self.use_item)

current_path = os.path.abspath(__file__)
father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
os.chdir(father_path)

auto_doctor = AutoDocter()
auto_doctor.start()


