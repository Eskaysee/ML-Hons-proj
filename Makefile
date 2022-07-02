compile:
	python3 setup.py install --force --user

hybrid: compile
	cd pyRoborobo_dev/examples; python3 NSmEDEA.py
	
pythonTut:
	cd pyRoborobo_dev/examples/
	python3 tutorial.py
	
ceeTut:
	cd build
	./roborobo -l config/tutorial.properties
	
clean:
	python3 setup.py clean --all

#activate:
#	conda activate roborobo
