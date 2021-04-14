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
CLOSE = 7

TIME_OUT = 100

IMG = (START, START2, ENERGY, END, RUN, STONE_ENERGY, CLOSE)

class AutoDocter():

	def __init__(self):
		self.img = {}
		self.device = None
		self.status = 0

		self.times = 0
		self.use_item = {"stone":0, "energy":0}
		self.time_out = 0

	def log(self, *args):
		print(*args)
		with open("./log.txt", "a", encoding="utf8") as f:
			f.writelines([str(arg) for arg in args] + ["\n"])

	def init_config(self):
		self.log("init_config")
		with open("./config.ini", "r", encoding="utf8") as f:
			for line in f.readlines():
				if line.startswith("#"):
					continue
				config = line.strip("\n").split("=")
				setattr(self, config[0], int(config[1]))
		self.ip_address = "127.0.0.1:" + str(self.port)

	def init_device(self):
		self.log("init_device")
		try:
			self.device = u2.connect(self.ip_address)
		except Exception:
			self.init_adb_connect()
			self.device = u2.connect(self.ip_address)

	def init_img(self):
		self.log("init_img")
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

		self.img[CLOSE]["img"] = cv2.imread(r'.\img\close.png')
		self.img[CLOSE]["size"] = self.img[CLOSE]["img"].shape[:2]

	def init_adb_connect(self):
		self.log("init_adb_connect")
		os.system(r'.\adb\adb.exe kill-server ')
		os.system(r'.\adb\adb.exe start-server ')
		os.system(r'.\adb\adb.exe connect '+self.ip_address)

	def click(self,x, y):
		self.device.click(x,y)
		self.time_out = 0

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
		if self.time_out >= TIME_OUT:
			return "time_out"
		self.device.screenshot(r".\img\screenshot.png")
		self.img_screen = cv2.imread(r'.\img\screenshot.png')
		if self.status == 0:
			res_start, x, y = self.search_returnPoint(self.img_screen, START)
			if res_start is not None:
				self.click(x,y)
				self.status += 1

		elif self.status == 1:
			res_start2, x1, y1 = self.search_returnPoint(self.img_screen, START2)
			res_energy, x2, y2 = self.search_returnPoint(self.img_screen, ENERGY)
			res_stone, x3, y3 = self.search_returnPoint(self.img_screen, STONE_ENERGY)
			if res_start2 is not None:
				self.click(x1,y1)
				self.status += 1
			elif res_stone is not None:
				if self.use_stone:
					self.click(x2,y2)
					self.status -= 1
					self.use_stone -= 1
					self.use_item["stone"] += 1
					self.log("use stone")
				else:
					return "stone_energy_out, {}".format(self.use_stone)
			elif res_energy is not None:
				if self.use_energy:
					self.click(x2,y2)
					self.status -= 1
					self.use_item["energy"] += 1
					self.log("use energy")
				else:
					return "energy_out"
			
		elif self.status == 2:
			res_end, x, y = self.search_returnPoint(self.img_screen, END)
			if res_end is not None:
				time.sleep(2)
				self.click(x,y)
				self.status = 0
				self.limit_times -= 1
				self.times += 1
				self.log(self.times)
			else:
				time.sleep(5)

	def close(self):
		res_close, x, y = self.search_returnPoint(self.img_screen, CLOSE)
		if res_close is not None:
			self.click(x,y)
			self.status -= 1

	def start(self):
		self.log("-"*15+" start "+"-"*15)
		self.init_config()
		self.init_device()
		self.init_img()
		
		res = ""
		self.log("start_loop")
		while self.limit_times and not res:
			res = self.run_loop()
			if res:
				self.close()
			if self.forever and res:
				self.log("forever_wait...")
				res = ""
				time.sleep(self.forever_time*60)
			time.sleep(1)
			self.time_out += 1
		self.log(res)
		self.log(self.use_item)
		self.log("-"*15+" end "+"-"*15)

current_path = os.path.abspath(__file__)
father_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
os.chdir(father_path)

auto_doctor = AutoDocter()
auto_doctor.start()


