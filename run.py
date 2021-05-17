import numpy as np
from simulate import Manager
import time
import os
import argparse


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-p', '--players', type=str, default='data/players.json', help='path to players.json file')
	parser.add_argument('-c', '--prices', type=str, default='data/prices.csv', help='path to scenario file (prices.csv)')
	parser.add_argument('-n', '--name', type=str, default='default', help='experiment name')
	parser.add_argument('-s', '--scenarios', type=int, default=1, help='number of runs')
	parser.add_argument('-t', '--team', type=str, default='team_PIR', help='team name')
	parser.add_argument('-r', '--regions', nargs='+', type=str, default=['all'], help='region names')
	args = parser.parse_args()
	import random
	random.seed(123)
	import numpy as np
	np.random.seed(123)

	name = args.name
	this_dir = os.path.dirname(os.path.abspath(__file__))
	t = time.time()

	if args.regions == ['all']:
		args.regions = [
			"grand_nord",
			"grand_est",
			"grand_rhone",
			"bretagne",
			"grand_ouest",
			"grand_sud_ouest",
			"grande_ardeche",
			"grand_sud_est"
		]

	manager = Manager(args.team, args.players, args.prices, args.regions)
	manager.simulate(args.scenarios, name)

