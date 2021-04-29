# python 3
#
# script for initializing the game from a players.json file
# optional improvements: git clone, perform tests


import os
import json
import argparse
from git import Repo, InvalidGitRepositoryError

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('-p', '--players', type=str, required=True, help='path to players.json file')
	parser.add_argument('-t', '--team', type=str, required=True, help='team name')
	args = parser.parse_args()

	this_dir = os.path.dirname(os.path.abspath(__file__))

	with open(args.players) as f:
		teams = json.load(f)

	players = teams.get(args.team, None)
	if players is None:
		print(f'team {args.team} does not exist')
	else:
		for val in players:
			data_path = os.path.join(this_dir, "data", args.team, val['folder'])
			code_path = os.path.join(this_dir, "players", args.team, val['folder'])
			# initialize data folders
			os.makedirs(data_path, exist_ok=True)

			# initialize player folders, git clone & test ?
			os.makedirs(code_path, exist_ok=True)

			try:
				# on essaie de puller le dépôt
				Repo(code_path).remotes.origin.pull()  # pull each player
			except InvalidGitRepositoryError as err:
				# ce n'est pas un dépôt git, on clone
				Repo.clone_from(val['url'], code_path)  #clone each player
