#!/usr/bin/python

from analytics import Analytics
import pygal
from datetime import datetime, timedelta, date
from fractions import gcd
import config

import Statsdash.utilities as utils

analytics = Analytics()
channel_ids = config.CHANNELS


class YoutubeData(object):

    def __init__(self, channels, period, frequency):
        """
        Set up data collection parameters
        Find time span using dates given
        """
        self.channels = channels
        self.period = period
        self.frequency = frequency
        self.previous = utils.StatsRange.get_previous_period(self.period, self.frequency)
        self.yearly = utils.StatsRange.get_previous_period(self.period, "YEARLY")
        self.date_list = [self.period, self.previous, self.yearly]
        
        self.channel_ids = utils.convert_values_list(channel_ids)

		
    def check_available_data(self):
        run_report = {"result":True, "channel":[]}
        for channel in self.channels:
        	ids = self.channel_ids[channel]
        	for id in ids:
        	    data_available = analytics.data_available(id, self.end.strftime("%Y-%m-%d"))
                if not data_available:
                    run_report['result'] = False
                    run_report['channel'] += channel			
        return run_report

		
    def country_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            table = []
            metrics = "views,estimatedMinutesWatched,subscribersGained,subscribersLost"
            for channel in self.channels:
                ids = self.channel_ids[channel]
                #results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics=metrics, dimensions="country", 
                #												filters="channel==%s" % id, max_results=None, sort="-estimatedMinutesWatched")		                									
                #rows = utils.format_data_rows(results)
                
                rows = analytics.rollup_ids(ids, date.get_start(), date.get_end(), metrics=metrics, dimensions="country", 
                												filters=None, max_results=None, sort="-estimatedMinutesWatched", aggregate_key="country")	
                for row in rows:
                    row =  utils.convert_to_floats(row, metrics.split(","))
                    row["subscriberChange"] = row["subscribersGained"] - row["subscribersLost"]
                table.extend(rows)
            	    			
            aggregated = utils.aggregate_data(table, (metrics + ",subscriberChange").split(","),  match_key="country")
            sorted = utils.sort_data(aggregated, "estimatedMinutesWatched", limit=20)
            data[count] = sorted
        
        added_change = utils.add_change(data[0], data[1], ["views","estimatedMinutesWatched","subscriberChange"], "previous", match_key="country")
        added_change = utils.add_change(added_change, data[2], ["views","estimatedMinutesWatched","subscriberChange"], "yearly", match_key="country")
        
        return added_change


    def channel_summary_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            table = []
            metrics="subscribersGained,subscribersLost,estimatedMinutesWatched"
            for channel_num, channel in enumerate(self.channels):
                ids = self.channel_ids[channel]

                if count == 0:
                    subscriber_count = analytics.rollup_stats(ids)['subscriberCount'] #only gets the current subscriber count
                elif count == 1:
                    #last period date, work out last periods subscriber count from current periods sub change 
                    this_channel = utils.list_search(data[0], "channel", channel)
                    subscriber_count = this_channel["subscriberCount"] - this_channel["subscriberChange"]
                else:
                    #don't need to work out yearly sub change 
                    subscriber_count = 0.0
                    
                #results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics=metrics, dimensions=None, filters="channel==%s" % id)	             
                #rows = utils.format_data_rows(results)
                rows = [analytics.rollup_ids(ids, date.get_start(), date.get_end(), metrics, dimensions=None, filters=None, sort=None, max_results=None, aggregate_key=None)]
                
                for row in rows:
                    row = utils.convert_to_floats(row, metrics.split(","))
                    row["channel"] = channel
                    row["subscriberChange"] = row["subscribersGained"] - row["subscribersLost"]
                    row["subscriberCount"] = float(subscriber_count)
                    
                table.extend(rows)
                
            aggregated = utils.aggregate_data(table, ["subscriberChange", "subscriberCount", "estimatedMinutesWatched"], match_key= "channel")
            sorted = utils.sort_data(aggregated, "estimatedMinutesWatched")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], ["subscriberChange", "subscriberCount", "estimatedMinutesWatched"], "previous", match_key= "channel")
        added_change = utils.add_change(added_change, data[2], ["subscriberChange", "estimatedMinutesWatched"], "yearly", match_key= "channel")
        
        return added_change
 
    
    def channel_stats_table(self):
        data = {}
        for count, date in enumerate(self.date_list):
            table = []
            #just subscribersGained to get number of subscribers per 1000 views 
            metrics="views,likes,dislikes,comments,shares,subscribersGained"
            for channel_num, channel in enumerate(self.channels):
                ids = self.channel_ids[channel]
                #results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics=metrics, dimensions=None, filters="channel==%s" % id)	
                #rows = utils.format_data_rows(results)
                
                rows = [analytics.rollup_ids(ids, date.get_start(), date.get_end(), metrics=metrics, dimensions=None)]
                
                for row in rows:
                    row = utils.convert_to_floats(row, metrics.split(","))
                    row["channel"] = channel
                    row["likeRate"] = utils.rate_per_1000(row["likes"], row['views'])
                    row["commentRate"] = utils.rate_per_1000(row["comments"], row['views'])
                    row["sharesRate"] = utils.rate_per_1000(row["shares"], row['views'])
                    row["subsRate"] = utils.rate_per_1000(row["subscribersGained"], row['views']) 
                    try:
                        row["likeRatio"] = utils.sig_fig(2, row["likes"] / row["dislikes"])
                    except ZeroDivisionError:
                        row["likeRatio"] = 0
                    try:
                        row["dislikeRatio"] = utils.sig_fig(2, row["dislikes"] / row["dislikes"])
                    except ZeroDivisionError:
                        row["dislikeRatio"] = 0                        
                
                table.extend(rows)
                           
            #aggregated = utils.aggregate_data(table, "channel", )
            sorted = utils.sort_data(table, "views")
            data[count] = sorted
            
        added_change = utils.add_change(data[0], data[1], ["views", "likeRate", "commentRate", "sharesRate", "subsRate", "likeRatio", "dislikeRatio"], "previous", match_key= "channel")
        added_change = utils.add_change(added_change, data[2], ["views", "likeRate", "commentRate", "sharesRate", "subsRate", "likeRatio", "dislikeRatio"], "yearly", match_key= "channel") 
        
        return added_change               

    def video_table(self):
        data = {}
        for count, date in enumerate([self.period]):
            table = []        
            for channel_num, channel in enumerate(self.channels):
                ids = self.channel_ids[channel]
                #results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics="estimatedMinutesWatched,views", dimensions="video", 
        		#									filters="channel==%s" % id, max_results="20", sort="-estimatedMinutesWatched")
                #rows = utils.format_data_rows(results)
                
                rows = analytics.rollup_ids(ids, date.get_start(), date.get_end(), metrics="estimatedMinutesWatched,views", dimensions="video", filters=None, max_results="20", 
                                                sort="-estimatedMinutesWatched", aggregate_key="video")
                for row in rows:
                    row = utils.convert_to_floats(row, ["estimatedMinutesWatched", "views"])
                    video_name = analytics.get_video(row['video'])
                    try:
                        row['title'] = video_name['items'][0]['snippet']['title']
                    except IndexError:
                        row["title"] = "Video Not Found" 
                    row['channel'] = channel	

                table.extend(rows)
            		
            aggregated = utils.aggregate_data(table, ["estimatedMinutesWatched", "views"], match_key="video")
            sorted = utils.sort_data(aggregated, "estimatedMinutesWatched", limit=10)
            data[count] = sorted
            #group

        
        #added_change = utils.add_change(data[0], data[1], "video", ["estimatedMinutesWatched", "views"], "DAILY")     
        
        return data[0]       			
        

    #TODO the traffic source breakdown epic    
    def traffic_source_table(self):
        data = {}
        source_types= ['ANNOTATION', 'EXT_URL', 'NO_LINK_OTHER', 'NOTIFICATION', 'PLAYLIST', 'RELATED_VIDEO', 'SUBSCRIBER', 'YT_CHANNEL', 'YT_OTHER_PAGE', 'YT_PLAYLIST_PAGE', 'YT_SEARCH']
        traffic_source = []
        for source in source_types:
            row = {"insightTrafficSourceType":source, "source_total":0.0}
            traffic_source.append(row)
        
        for count, date in enumerate(self.date_list):
            table = []
            for channel in self.channels:
                ids = self.channel_ids[channel]
                #results = analytics.run_analytics_report(start_date=date.get_start(), end_date=date.get_end(), metrics="estimatedMinutesWatched",
                #                                            dimensions="insightTrafficSourceType", filters="channel==%s" % id, sort="-estimatedMinutesWatched")	
                #rows = utils.format_data_rows(results)
                
                rows = analytics.rollup_ids(ids, date.get_start(), date.get_end(), metrics="estimatedMinutesWatched", dimensions="insightTrafficSourceType", filters=None, 
                                                sort="-estimatedMinutesWatched", aggregate_key="insightTrafficSourceType")
                
                channel_total = 0.0
                for row in rows:
                    row = utils.convert_to_floats(row, ["estimatedMinutesWatched"])
                    row["channel"] = channel
                    channel_total += row["estimatedMinutesWatched"]                    
                    
                new_rows = []
                for source_type in traffic_source:
                    try:
                        result = utils.list_search(rows, "insightTrafficSourceType", source_type["insightTrafficSourceType"])
                        result["channel_total"] = channel_total
                        new_rows.append(result)
                        source_type["source_total"] += result["estimatedMinutesWatched"]
                    except KeyError:
                        new_rows.append({"insightTrafficSourceType":source_type["insightTrafficSourceType"], "channel":channel, "channel_total":channel_total, "estimatedMinutesWatched":0.0})

                 
                #table is list of lists, list for each channel
                table.append(new_rows)
            
            #table = utils.sort_data(table, "channel_total")  
            
            new_table = []
            for channel in table:
                for row in channel:
                    #order each channel section by the total minutes watched for each source 
                    #calculate channels percentage breakdown by source
                    breakdown = utils.percentage(row["estimatedMinutesWatched"], row["channel_total"])
                    row["source_percentage"] = breakdown
                    result = utils.list_search(traffic_source, "insightTrafficSourceType", row["insightTrafficSourceType"])
                    row["source_total"] = result["source_total"]
                sort_row = utils.sort_data(channel, "source_total")  
                new_table.append(sort_row)
            
            #sort the new table of dictionaries by total channel watch time 
            #sorted = utils.sort_data(new_table, "channel_total")   

            sorted_list = sorted(new_table, key = lambda k: k[0]["channel_total"], reverse = True)
            data[count] = sorted_list       
            
            
        return data[0]            

            