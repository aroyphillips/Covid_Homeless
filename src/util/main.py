import pandas as pd
import matplotlib.pyplot as plt
import six
import numpy as np
import datetime

# to ignore pandas warnings
import warnings
warnings.filterwarnings("ignore")

class Main():
    def __init__(self):     
        hotel_data = pd.read_csv("../../data/hotel_data.csv", index_col=False)
        homeless_data = pd.read_csv("../../data/homeless_data.csv", index_col=False)
        minimum_wage_data = pd.read_csv("../../data/minimum_wage.csv", index_col=False)

        self.all_data = hotel_data.join(homeless_data.set_index("state"), on="state")\
            .join(minimum_wage_data.set_index("state"), on="state")

        # 2017 avg nightly hotel rate in US - https://www.businesstravelnews.com/Corporate-Travel-Index/2018/Demand-Drives-US-Hotels
        self.avg_hotel_rate = 180.12
        
        # percent of avg nightly rate
        self.percent_of_avg_nightly_fee = 0.40
        
        # Number of people in a single room
        self.people_per_room = 2
        
        # Number of employees required per 10 rooms to take care of homeless population
        self.num_employees_per_10_rooms = 1
        
        # inflation rate to pay hotel employees extra for working
        self.min_wage_inflation_percentage = 0.10
        
        # work day hours for a hotel employee
        self.work_day_hrs = 8

    def homeless_pop_vs_avail_rooms(self, bar_viz=False):
        """
        The effect of sheltering the entire homeless population into separate rooms out of all available hotel rooms
        
        :param viz: boolean - display a bar graph of data (default False) - saves plot to img directory
        
        :return: dataframe with State and Percent of Rooms Occupied By Homeless Population (percent_comp)
        """
        df = self.all_data[["state", "num_avail_rooms", "tot_homeless_population"]]
        
        df["percent_comp"] = (df["tot_homeless_population"] / self.people_per_room) / df["num_avail_rooms"]
    
        # -----------PLOTTING------------------#
        if bar_viz:
            df_viz = df[["state", "percent_comp"]]
            ax = df_viz.plot.bar(x='state', y='percent_comp', rot=90, figsize=(15,8), legend=False)
            plt.title("The Effect of Sheltering the Homeless Population into All Available Hotel Rooms ({} people per room)"
                      .format(self.people_per_room), pad=20)
            plt.xlabel("State", labelpad=15)
            plt.ylabel("Percent of Rooms Occupied By Homeless Population", labelpad=15)
            plt.subplots_adjust(bottom=0.25)
            plt.savefig("../../img/all_homeless_in_all_rooms_percentage.png")
            plt.show()
        
        return df[["state", "percent_comp"]]

    def number_of_rooms_reserved(self, bar_viz=False):
        """
        Produces a dataframe mapping each state to the number of reserved rooms that would be required to house the homeless
        population given a certain number of people per room.
        
        :param viz: boolean - displays a bar graph (default False) - saves plot to img directory
        
        :return: dataframe with state and number of reserved rooms
        """
        df = self.all_data[["state", "num_avail_rooms"]]
        reserve_percent_df = self.homeless_pop_vs_avail_rooms()
        df = df.join(reserve_percent_df.set_index("state"), on="state")
        
        df["num_reserved_rooms"] = round(df["percent_comp"] * df["num_avail_rooms"])
        df["num_reserved_rooms"] = df["num_reserved_rooms"].apply(lambda x: int(x))
    
        # -----------PLOTTING------------------#
        if bar_viz:
            df_viz = df[["state", "num_reserved_rooms"]]
            ax = df_viz.plot.bar(x='state', y='num_reserved_rooms', rot=90, figsize=(15, 8), legend=False)
            plt.title("Number of Reserved Rooms Per State by Homeless Population Composition")
            plt.xlabel("State", labelpad=15)
            plt.ylabel("Number of Rooms", labelpad=15)
            plt.subplots_adjust(bottom=0.25, right=0.95, left=0.10)
            plt.savefig("../../img/num_reserved_rooms.png")
            plt.show()
    
        return df[["state", "num_reserved_rooms"]]

    def daily_employee_cost(self, table_viz=False, bar_viz=False):
        """
        Outputs a dataframe that maps each state to the total cost needed to pay for employees
        
        :param table_viz: display table of dataframe
        :param bar_viz: display the dataframe in a bar graph
        
        :return: dataframe with columns: state,  tot_daily_employee_cost
        """
        df = self.all_data[["state", "minimum_wage"]]
        rooms_reserved_df = self.number_of_rooms_reserved()
        df = df.join(rooms_reserved_df.set_index("state"), on="state")
        
        df["num_employees_needed"] = (self.num_employees_per_10_rooms/10) * df["num_reserved_rooms"]
        df["num_employees_needed"] = df["num_employees_needed"].apply(lambda x: np.math.ceil(x))
    
        df["final_hrly_wage"] = round((1 + self.min_wage_inflation_percentage) * df["minimum_wage"], 2)
        df["tot_daily_employee_cost"] = (self.work_day_hrs * df["final_hrly_wage"]) * df["num_employees_needed"]
    
        sum = df["tot_daily_employee_cost"].sum()
    
        if bar_viz:
            df_viz = df[["state", "tot_daily_employee_cost"]]
            ax = df_viz.plot.bar(x='state', y='tot_daily_employee_cost', rot=90, figsize=(15, 8), legend=False)
            plt.title("Employee Cost Per Day - {} employees per 10 rooms - {}% Minimum Wage Inflation"
                      .format(self.num_employees_per_10_rooms, 100 * self.min_wage_inflation_percentage))
            plt.xlabel("State", labelpad=15)
            plt.ylabel("Cost ($)", labelpad=15)
        
            xmin, xmax, ymin, ymax = plt.axis()
            plt.text(0.75 * xmax, 0.80 * ymax, "Total National Daily Cost = ${:,.2f}".format(sum), size=15, rotation=0.,
                     ha="center", va="center",
                     bbox=dict(boxstyle="round",
                               ec=(1., 0.5, 0.5),
                               fc=(1., 0.8, 0.8),
                               )
                     )
            plt.subplots_adjust(bottom=0.25, right=0.95, left=0.10)
            plt.savefig("../../img/daily_employee_cost.png")
            plt.show()
    
        if table_viz:
            df_new = df[["state", "tot_daily_employee_cost"]]
        
            tot_row = ["TOTAL", sum]
            df_new.loc[len(df_new)] = tot_row
            # df_new.append(pd.DataFrame(tot_row, columns=["state", "tot_daily_employee_cost"]))
        
            df_new["tot_daily_employee_cost"] = df_new["tot_daily_employee_cost"].apply(lambda x: "${:,.2f}".format(x))
            df_new.rename(columns={"state": "State", "tot_daily_employee_cost": "Employee Cost Per Day"}, inplace=True)
            ax = self.__display_df(df_new, col_width=3.8)
        
            plt.title("Employee Cost Per Day \n {} employees per 10 rooms - {}% Minimum Wage Inflation"
                      .format(self.num_employees_per_10_rooms, 100 * self.min_wage_inflation_percentage)
                      , pad=20)
            plt.subplots_adjust(top=.95, bottom=0.02)
            plt.savefig("../../img/daily_employee_cost_table.png")
            plt.show()
            
        return df[["state", "tot_daily_employee_cost"]]
    
    def daily_guest_fee(self, table_viz=False, bar_viz=False):
        """
        Outputs a dataframe that maps each state to the total cost needed to pay hotles for offering rooms
        
        :param table_viz: display table of dataframe
        :param bar_viz: display the dataframe in a bar graph
        
        :return: dataframe with columns: state,  guest_fee
        """
        df = self.number_of_rooms_reserved()
        
        nightly_fee = self.avg_hotel_rate * self.percent_of_avg_nightly_fee
        df["guest_fee"] = round(df["num_reserved_rooms"] * nightly_fee, 2)
    
        sum = df["guest_fee"].sum()
    
        if bar_viz:
            df_viz = df[["state", "guest_fee"]]
            ax = df_viz.plot.bar(x='state', y='guest_fee', rot=90, figsize=(15, 8), legend=False)
            plt.title("Guest Fee Per Day - Nightly Rate = ${:,.2f} \n (Avg National Nightly Rate = ${:,.2f})"
                      .format(nightly_fee, self.avg_hotel_rate))
            plt.xlabel("State", labelpad=15)
            plt.ylabel("Cost ($)", labelpad=15)
        
            xmin, xmax, ymin, ymax = plt.axis()
            plt.text(0.75 * xmax, 0.80 * ymax, "Total National Daily Cost = ${:,.2f}".format(sum), size=15, rotation=0.,
                     ha="center", va="center",
                     bbox=dict(boxstyle="round",
                               ec=(1., 0.5, 0.5),
                               fc=(1., 0.8, 0.8),
                               )
                     )
            plt.subplots_adjust(bottom=0.25, right=0.95, left=0.10)
            plt.savefig("../../img/daily_guest_fee_cost.png")
            plt.show()
            
        if table_viz:
            df_new = df[["state", "guest_fee"]]
        
            tot_row = ["TOTAL", sum]
            df_new.loc[len(df_new)] = tot_row
        
            df_new["guest_fee"] = df_new["guest_fee"].apply(lambda x: "${:,.2f}".format(x))
            df_new.rename(columns={"state": "State", "guest_fee": "Guest Fee Per Day"}, inplace=True)
            ax = self.__display_df(df_new, col_width=3.8)
        
            plt.title("Guest Fee Per Day - Nightly Rate = ${:,.2f} \n (Avg National Nightly Rate = ${:,.2f})"
                      .format(nightly_fee, self.avg_hotel_rate)
                      , pad=20)
            plt.subplots_adjust(top=.95, bottom=0.02)
            plt.savefig("../../img/daily_guest_fee_table.png")
            plt.show()
            
        return df[["state", "guest_fee"]]

    def total_daily_state_costs(self, table_viz=False, bar_viz=False):
        """
        Computes the total daily cost for each state
        
        :param table_viz: display the dataframe visual
        :param bar_viz: display the dataframe as a bar graph
        
        :return: a dataframe with columns: state, total
        """
        
        employee_cost_df = self.daily_employee_cost()
        guest_fee_df = self.daily_guest_fee()
        
        df = employee_cost_df.join(guest_fee_df.set_index("state"), on="state")
    
        df['total'] = df.iloc[:, 1:].sum(axis=1)
        
        sum_emp = df["tot_daily_employee_cost"].sum()
        sum_guest = df["guest_fee"].sum()
        sum_tot = df["total"].sum()
    
        if bar_viz:
            df_viz = df[["state", "total"]]
            ax = df_viz.plot.bar(x='state', y='total', rot=90, figsize=(15, 8), legend=False)
            
            plt.xlabel("State", labelpad=15)
            plt.ylabel("Cost ($)", labelpad=15)
            plt.title("Total Daily Cost \n {} employees per 10 rooms - {}% Minimum Wage Inflation \n "
                      "Nightly Rate = ${:,.2f} ({}% of National Avg)"
                      .format(self.num_employees_per_10_rooms, 100 * self.min_wage_inflation_percentage,
                              self.avg_hotel_rate * self.percent_of_avg_nightly_fee, self.percent_of_avg_nightly_fee * 100)
                      , pad=20)
            xmin, xmax, ymin, ymax = plt.axis()
            plt.text(0.75 * xmax, 0.80 * ymax, "Total National Daily Cost = ${:,.2f}".format(sum_tot), size=15, rotation=0.,
                     ha="center", va="center",
                     bbox=dict(boxstyle="round",
                               ec=(1., 0.5, 0.5),
                               fc=(1., 0.8, 0.8),
                               )
                     )
            plt.subplots_adjust(bottom=0.25, right=0.95, left=0.10)
            plt.savefig("../../img/total_daily_cost.png")
            plt.show()
    
    
        if table_viz:
            df_new = df.copy()
            tot_row = ["TOTAL", sum_emp, sum_guest, sum_tot]
            df_new.loc[len(df)] = tot_row
    
            df_new["tot_daily_employee_cost"] = df_new["tot_daily_employee_cost"].apply(lambda x: "${:,.2f}".format(x))
            df_new["guest_fee"] = df_new["guest_fee"].apply(lambda x: "${:,.2f}".format(x))
            df_new["total"] = df_new["total"].apply(lambda x: "${:,.2f}".format(x))
    
            df_new.rename(columns={"state": "State",
                               "tot_daily_employee_cost": "Employee Cost Per Day",
                               "guest_fee": "Guest Fee Per Day",
                               "total": "Total Daily Cost"}, inplace=True)
            ax = self.__display_df(df_new, col_width=3.8)
        
            plt.title("Total Daily Cost \n {} employees per 10 rooms - {}% Minimum Wage Inflation \n "
                      "Nightly Rate = ${:,.2f} ({}% of National Avg)"
                      .format(self.num_employees_per_10_rooms, 100 * self.min_wage_inflation_percentage,
                              self.avg_hotel_rate * self.percent_of_avg_nightly_fee, self.percent_of_avg_nightly_fee * 100)
                      , pad=20)
            plt.subplots_adjust(top=.92, bottom=0.02)
            plt.savefig("../../img/total_daily_cost_table.png")
            plt.show()
        
        return df[["state", "total"]]

    def durational_total_state_costs(self, table_viz=True):
        """
        Computes the total cost for states over different periods of time (1, 15, 30, 45, 60 days)
        
        :param table_viz: display the dataframe visual
        
        :return: dataframe with columns: state, 1_day, 15_days, 30_days, 45_days, 60_days
        """
        today = datetime.datetime.today()
        days_1 = today + datetime.timedelta(days=1)
        days_15 = today + datetime.timedelta(days=15)
        days_30 = today + datetime.timedelta(days=30)
        days_45 = today + datetime.timedelta(days=45)
        days_60 = today + datetime.timedelta(days=60)
        
        df = self.total_daily_state_costs()
        
        
        df["15_days"] = df["total"] * 15
        df["30_days"] = df["total"] * 30
        df["45_days"] = df["total"] * 45
        df["60_days"] = df["total"] * 60
        
        df.rename(columns={"total":"1_day"}, inplace=True)
    
        sum_1 = df["1_day"].sum()
        sum_15 = df["15_days"].sum()
        sum_30 = df["30_days"].sum()
        sum_45 = df["45_days"].sum()
        sum_60 = df["60_days"].sum()
        
        df_out = df[["state", "1_day", "15_days", "30_days", "45_days", "60_days"]]
        
        if table_viz:
            df_out.rename(columns={"state": "State", "1_day": "1 Night ({})".format(days_1.strftime("%b %d")),
                                   "15_days": "15 Nights ({})".format(days_15.strftime("%b %d")),
                                   "30_days": "30 Nights ({})".format(days_30.strftime("%b %d")),
                                   "45_days": "45 Nights ({})".format(days_45.strftime("%b %d")),
                                   "60_days": "60 Nights ({})".format(days_60.strftime("%b %d"))},inplace=True)
            tot_row = ["TOTAL", sum_1, sum_15, sum_30, sum_45, sum_60]
            df_out.loc[len(df)] = tot_row
        
            for idx in range(1, len(list(df_out.columns))):
                cols = list(df_out.columns)
                df_out[cols[idx]] = df_out[cols[idx]].apply(lambda x: "${:,.2f}".format(x))
                
            
            ax = self.__display_df(df_out, col_width=10.8)
        
            plt.title("Total Durational Costs \n Today: {}".format(today.strftime("%b %d, %Y"))
                      , pad=20)
            plt.subplots_adjust(top=.95, bottom=0.02, left=0.02, right=0.98)
            plt.savefig("../../img/durational_total_costs_table.png")
            plt.show()
            
        return df_out
    
    def daily_cost_for_state(self, state):
        """
        Print the daily cost for the specified state
        
        :param state:
        
        :return: None
        """
        df = self.daily_employee_cost()
        
        df = df[["state", "tot_daily_employee_cost"]]
        
        df = df[df["state"].apply(lambda x: x.lower()) == state.lower()]
        
        state_cost = df["tot_daily_employee_cost"].values[0]
        
        formatted_state_cost = "${:,.2f}".format(state_cost)
        
        print("Daily cost for the state of " + state + " = " +formatted_state_cost)

    def __display_df(self, data, col_width=3.0, row_height=0.625, font_size=14,
                         header_color='#40466e', row_colors=['#f1f1f2', 'w'], edge_color='w',
                         bbox=[0, 0, 1, 1], header_columns=0,
                         ax=None, **kwargs):
        """
        Produces a readable and organized visualization for a dataframe
        """
        if ax is None:
            size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
            size[0] = 15.2
            size[1] = 0.6 * size[1]
            fig, ax = plt.subplots(figsize=size)
            ax.axis('off')
    
        mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)
    
        mpl_table.auto_set_font_size(False)
        mpl_table.set_fontsize(font_size)
    
        for k, cell in six.iteritems(mpl_table._cells):
            cell.set_edgecolor(edge_color)
            if k[0] == 0 or k[1] < header_columns:
                cell.set_text_props(weight='bold', color='w')
                cell.set_facecolor(header_color)
            else:
                cell.set_facecolor(row_colors[k[0]%len(row_colors) ])
                
        return ax


if __name__ == "__main__":
    m = Main()
    # m.homeless_pop_vs_avail_rooms(bar_viz=True)
    # m.number_of_rooms_reserved(bar_viz=True)
    # m.daily_employee_cost(table_viz=True, bar_viz=True)
    # m.daily_guest_fee(table_viz=True, bar_viz=True)
    
    # m.total_daily_state_costs(table_viz=True, bar_viz=True)
    
    # m.durational_total_state_costs(table_viz=True)
    # m.daily_cost_for_state("Texas")