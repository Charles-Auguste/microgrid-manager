# python 3
import json
import numpy as np
import random
import os
from collections import defaultdict
import pandas
import tqdm
import matplotlib.pyplot as plt


class Manager:
    def __init__(self, team_name: str, path_to_player_file, path_to_price_file):
        self.horizon = 48
        self.dt = 0.5
        self.nbr_iterations = 50
        self.nb_pdt = int(self.horizon/self.dt)

        self.nb_tot_players = 0
        self.nb_players = defaultdict(int)

        self.players = self.create_players(team_name, path_to_player_file)
        self.scenarios = self.read_all_scenarios()
        self.external_prices = {"purchase": np.zeros(self.horizon), "sale": np.zeros(self.horizon)}

        self.__results = defaultdict(dict)

    def create_players(self, team_name: str, json_file):
        """initialize all players"""

        with open(json_file) as f:
            teams = json.load(f)

        new_players = []

        players = teams.get(team_name, None)
        if players is None:
            raise ValueError(f'team {team_name} is not found')

        for player in players:
            self.nb_players[player['type']] += 1
            player['team'] = team_name
            mod = __import__(f"players.{team_name}.{player['folder']}.player", fromlist=["Player"])
            new_player = mod.Player()
            new_player.__manager__data = player
            new_players.append(new_player)

        return new_players

    def read_all_scenarios(self):
        """initialize daily scenarios"""

        this_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(this_dir, "scenarios")
        # les scenarios pour chaque type de player
        scenario = {}

        for player in self.players:
            player_type = player.__manager__data["type"]
            if player_type == "charging_station":
                
                #STATION DE RECHARGE
                car_data=pandas.read_csv(os.path.join(data_dir,"ev_scenarios.csv" ),delimiter = ";")
                nb_car=10
                charging_station={}
                for day in range (365):
                    day_name="scenario_"+str(day+1)
                    day_data={}
                    for car in range (10):
                        car_name="car_"+str(car+1)
                        car_dep_arr=[car_data["time_slot_dep"][10*day+car],car_data["time_slot_arr"][10*day+car]]
                        day_data[car_name]=car_dep_arr
                    charging_station[day_name]=day_data
                scenario[player_type]=charging_station

                #================================================================================================================================================================
                # pour acceder aux horaires de départ et d'arrivée d'une voiture pendant une journée : scenario["charging_station"]["scenario_i"]["car_j"]  --> renvoie une liste
                #================================================================================================================================================================

            elif player_type == "solar_farm":
                
                # FERME SOLAIRE
                solar_data=pandas.read_csv(os.path.join(data_dir,"pv_prod_scenarios.csv" ),delimiter = ";")
                # 8 régions, 365 jours, 24 heures
                scenario_solar={}
                for region in range (8):
                    region_name="region_"+str(region+1)
                    reg={} 
                    for jour in range (365):
                        day_name="scenario_"+str(jour+1)
                        list_day=[]
                        for heure in range (24):
                            list_day.append(solar_data["pv_prod (W/m2)"][8760*region+24*jour+heure])
                        reg[day_name]=list_day
                    scenario_solar[region_name]=reg
                scenario[player_type]=scenario_solar


                #======================================================================================================
                # pour acceder à une journée : scenario["solar_farm"]["region_i"]["scenario_j"]  --> renvoie une liste
                #======================================================================================================

            else:
                
                # COMPLEXE INDUSTRIEL
                industrial_data=pandas.read_csv(os.path.join(data_dir,"indus_cons_scenarios.csv" ),delimiter = ";")
                nb_scenarios=0
                for i in industrial_data.index:
                    if(industrial_data["time_slot"][i]==1):
                        nb_scenarios+=1
                scenario_industrial={}
                for i in range (nb_scenarios):
                    nom_scenario="scenario_"+str(i+1)
                    list_scenario=[]
                    for j in range (48):
                        list_scenario.append(industrial_data["cons (kW)"][48*i+j])
                    scenario_industrial[nom_scenario]=list_scenario
                scenario[player_type]=scenario_industrial

                #===============================================================================================
                # pour acceder à une journée : scenario["industrial_farm"]["scenario_i"]  --> renvoie une liste
                #===============================================================================================

        return scenario

    def initialize_prices(self):
        """initialize daily prices"""
        purchase_prices=np.zeros(self.horizon)
        sale_prices=np.zeros(self.horizon)
        purchase_0=1
        sale_0=1
        for i in range (self.horizon):
            purchase_prices[i]=purchase_0
            sale_prices[i]=sale_0
        return {"purchase": purchase_prices, "sale": sale_prices}

    def draw_random_scenario(self):
        """ Draw a scenario for the day """
        scenario = {}
        for player in self.players:
            player_type = player.__manager__data["type"]
            if (player_type=="solar_farm"):
                nb_region=random.randint(1,8)
                nb_scenario=random.randint(1,365)
                random_scenario=self.scenarios["solar_farm"]["region_"+str(nb_region)]["scenario_"+str(nb_scenario)]
                scenario[player_type] = random_scenario
            elif (player_type=="charging_station"):
                nb_scenario=random.randint(1,365)
                random_scenario=self.scenarios["charging_station"]["scenario_"+str(nb_scenario)]
                scenario[player_type] = random_scenario
            else:
                nb_scenario=random.randint(1,90)
                random_scenario=self.scenarios["industrial_farm"]["scenario_"+str(nb_scenario)]
                scenario[player_type] = random_scenario            
        return scenario

    def get_microgrid_load(self):
        """ Compute the energy balance on a slot """
        microgrid_load = np.zeros(self.nb_pdt)
        loads = {}

        for player in self.players:
            load = player.compute_load()

            microgrid_load += np.max(load, 0)
            # storing loads for each player for future backup
            loads[player] = load

        return microgrid_load, loads

    def compute_bills(self, microgrid_load, loads):
        """ Compute the bill of each players """
        microgrid_bill = 0
        player_bills = np.zeros(len(self.players))
        for i in range (self.horizon):
            microgrid_bill=microgrid_load[i]*self.prices("purchase")[i]
            for j in range (len(self.players)):
                player=self.player[j]
                for i in range (self.horizon):
                    player_bills[j]+=self.prices("purchase")[i]*loads[player][i]
        return microgrid_bill, player_bills

    def send_prices_to_players(self, initial_prices):
        for player in self.players:
            # TODO: a remplacer
            player.set_prices(initial_prices)
            pass

    def send_scenario_to_players(self, scenario):
        for player in self.players:
            # TODO: a remplacer
            #player.set_scenario(scenario)
            pass

    def play(self, simulation):
        """ Playing one party """
        self.reset()
        # initialisation de la boucle de coordination
        scenario = self.draw_random_scenario()
        self.send_scenario_to_players(scenario)
        prices = self.initialize_prices()
        # debut de la coordination
        for iteration in range(self.nbr_iterations):  # main loop
            self.send_prices_to_players(prices)
            microgrid_load, player_loads = self.get_microgrid_load()
            microgrid_bill, player_bills = self.compute_bills(microgrid_load, player_loads)
            self.store_results(simulation, iteration,
                               {
                                   'scenario': scenario,
                                   'player_loads': player_loads,
                                   'player_bills': player_bills,
                                   'microgrid_load': microgrid_load,
                                   'microgrid_bill': microgrid_bill
                               }
                               )
            prices, converged = self.get_next_prices(iteration, prices, microgrid_load)
            if converged:
                break

    def get_next_prices(self, iteration, prices, microgrid_load):
        K=1 #facteur de pénalisation
        old_purchase=prices.get("purchase")
        old_sale=prices.get("sale")
        purchase_prices = np.zeros(self.horizon)
        sale_prices = np.zeros(self.horizon)
        purchase_0 = 1
        sale_0 = 1
        for i in range (self.horizon):
            purchase_prices[i]=purchase_0+K*microgrid_load[i]
            sale_prices[i]=sale_0+K*microgrid_load[i]
        converge=true
        epsilon=0.1
        for i in range (self.horizon):
            if (abs(old_purchase[i]-purchase_prices[i])+abs(old_sale[i]-sale_prices[i])>epsilon):
                converge=false
        new_prices={"purchase": purchase_prices, "sale": sale_prices}
        return new_prices, converge

    def store_results(self, simulation, iteration, data):
        self.__results[simulation][iteration] = data

    def reset(self):
        # reset the attributes of the manager
        for player in self.players:  # reset the attributes of thes players
            player.reset()

    def simulate(self, nb_simulation, simulation_name):
        # for each simulation
        for simulation_number in tqdm.range(nb_simulation):
            self.play(simulation_number)

        self.reset()

        self.data_viz(self.__results)

    def data_viz(self, data):
        pass
