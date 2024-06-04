compile:
	python3 setup.py install --force --user;

Env:
	cd pyRoborobo_dev/examples; python3 Env.py random; python3 Env.py fitness; python3 Env.py hybrid
	
hybrid:
	cd pyRoborobo_dev/examples; python3 Env.py hybrid
	
observe:
	cd pyRoborobo_dev/examples/results; cat Testing.txt
	
pythonTut:
	cd pyRoborobo_dev/examples
	python3 tutorial.py
	
ceeTut:
	cd build
	./roborobo -l config/tutorial.properties
	
clean:
	python3 setup.py clean --all
	cd pyRoborobo_dev/examples; rm -rf results/*

#activate:
#	conda activate roborobo
#	export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6
