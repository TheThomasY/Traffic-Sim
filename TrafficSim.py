# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 17:19:48 2020

@author: thoma
"""

import numpy as np
from numpy import random, sin, cos, pi
import matplotlib.pyplot as plt
import h5py


class Road():
    
    def __init__(self, name, length=200, speed_limit=6,\
                 density=0.20, slow_probability=0.25, closed_loop=True):
        
        self.name = name                    # Road Name - REQUIRED
        self.L = length                     # Integer - Road length - [5m]
        self.limit = speed_limit            # Integer - Speed Limit - [5ms-1]
        self.density = density              # Float - Initial Car Density
        self.slow_prob = slow_probability   # Float - Probability of slowing
        self.closed = closed_loop           # Boolean - Is road a loop



# --- Road Generation ---        
                
def Generate_Busy_Road(Road, start_speed=0):
    """Road is an object of class Road()."""
    
    road_array = np.zeros(Road.L)-1    # -1 represents an empty space - no car    
    No_Of_Cars = Road.L * Road.density

    n = 0 
    while n < No_Of_Cars:
        # Assign cars to random spaces on the road until the specified density is reached
        site = np.random.randint(0,Road.L)
        if road_array[site] == (-1):
            road_array[site] = start_speed
            n += 1
            
    return road_array



# --- Car Management Functions ---

def Spaces_Ahead(road, road_array, site):
    """Returns number of spaces ahead of a car with regard to its speed"""
    
    for i in range(road.limit-1):
        if road_array[(site+i+1)%road.L] != -1:
            return i
    return road.limit-1



def Accel(road, road_array):
    """Accelerates the cars which are able to"""
    
    for i in range(road.L):
        if road_array[i] != -1 and road_array[i] < road.limit:
        # If there is a car and its speed is below the limit    
            if road_array[i] < Spaces_Ahead(road,road_array, i):
            # If there is enough space ahead for the car to accelerate    
                road_array[i] += 1  
            if road_array[i] > Spaces_Ahead(road,road_array, i):
            # If there is not space ahead for car to accelerate
                road_array[i] = Spaces_Ahead(road,road_array, i)
                # Reduce car's speed so that it doesn't hit the car ahead
                
        if road_array[i] > 0:
            # Check if there is a moving car
            slow_random_No = random.uniform(0,1)     
            # Random decimal between 0 and 1, then check if it is less than the probability of a car slowing:
            if slow_random_No < road.slow_prob:
                road_array[i] -= 1      # If yes, reduce speed by one unit
                
    return road_array


    
def Move(road, road_array):
    """Moves all cars on road for one unit of time"""
            
    loop_stop = -1
    
    for i in range(road.L-1, -1, -1):
        car_speed = int(road_array[i])
        
        if car_speed > 0:
            road_array[(i+car_speed)%road.L] = road_array[i]    # Move car
            road_array[i] = -1             # Remove car from previous position
            
            # Below prevents moving the same car twice if it travels from end to start of the array.  
            if i > road.L-1-road.limit and (i+car_speed)%road.L < road.limit\
            and loop_stop == -1:
                loop_stop = (i+car_speed)%road.L + 1
        if i == loop_stop:
            break
        
    return road_array
        

def Run_Road(road, road_array, Time, watch_cars=False):
    """ Run simulation on a road for Time seconds of simulation time"""
    
    moved_road = road_array
    
    with h5py.File('Write_{}.hdf5'.format(road.name),'w') as f:
        f.create_dataset('Road_at_time_0', data = moved_road)
    
    for t in range(Time):
        acceled_road = Accel(road, moved_road)
        moved_road = Move(road, acceled_road)
        
        with h5py.File('Write_{}.hdf5'.format(road.name),'a') as f:
            f.create_dataset('Road_at_time_{}'.format(t+1), data = moved_road)
            # Write the road array at each time t to a HDF5 file
        
        if watch_cars:
            show_road(road, moved_road)
        
    return moved_road



# --- Dataset Extraction --- 

def Dataset_To_Array(road, time):
    """ Opens HDF5 file and converts into array at given time"""
    
    with h5py.File('Write_{}.hdf5'.format(road.name),'r') as f:
        #print("Keys: %s" % f.keys())                          # Print Keys
        road_data_t = f['Road_at_time_{}'.format(time)]        # Dataset
        road_array_t = road_data_t[:]                          # Array

    return road_array_t


    
#--- Visualisation of Car Positions ---

def show_road(road, road_array):

    ycirc = np.zeros(road.L)
    xcirc = np.zeros(road.L)
    
    for i in range(road.L):
        if road_array[i] != (-1):
            ycirc[i] = sin((i*2*pi)/road.L)
            xcirc[i] = cos((i*2*pi)/road.L)
            
    theta = np.linspace(0, 2*np.pi, 100)
    r = np.sqrt(1.0)
    x1 = r*np.cos(theta)
    x2 = r*np.sin(theta)
    fig, ax = plt.subplots(1)
    ax.plot(x1, x2)
    ax.scatter(xcirc, ycirc, color='orange')
    ax.set_aspect(1)
    plt.xlim(-1.25,1.25)
    plt.ylim(-1.25,1.25)
    plt.axis('off')
    plt.show()
    
    



def Locations_And_Speed_Arrays(road_array):
    """Returns 2 arrays: the locations and speeds of every car on a road respectively"""
    
    total_cars = (road_array > -1).sum()     # Total number of cars on road
    car_locations = np.zeros(total_cars)
    car_speeds = np.zeros(total_cars)
    n = 0
    
    for i in range(len(road_array)):
        if road_array[i] != -1:
            car_locations[n] = i
            car_speeds[n] = road_array[i]
            n += 1
    
    return [car_locations, car_speeds]
   

def Generate_Heatmap(road, Time):
    """ Generates a graphical heatmap for cars on the road over time based on their speeds and locations"""
    
    cm = plt.cm.get_cmap('hot')     # "Fire Effect" colourmap
    
    for t in range(Time):
        road_t = Dataset_To_Array(road, t)      # Extract road array at time t
        locations_speeds = Locations_And_Speed_Arrays(road_t)
        locations = locations_speeds[0]         # Car locations in array
        speeds = locations_speeds[1]            # Car speeds in array
        total_cars = (road_t > -1).sum()        # Total number of cars on road
        
        sc = plt.scatter(np.zeros(total_cars)+t, locations, c=speeds, vmin=0, vmax=6, cmap=cm)      # The scatter plot: x=time, y=car location, colour=speed
    
    plt.colorbar(sc)
    plt.show()
    
    

#--- Run Simulation ---
   
Road1 = Road(name="Road1")
Road2 = Road(name="Road2")

R1 = Generate_Busy_Road(Road1)  
R2 = Generate_Busy_Road(Road2)  
# Arrays Containing initial car positions/speeds
    
Time = 60              # Total in-simulation time [s]
 
show_road(Road1, R1)    # Show inital state of the road
show_road(Road2, R2)    # Show inital state of the road

final_road1 = Run_Road(Road1, R1, Time, watch_cars=False)
final_road2 = Run_Road(Road2, R2, Time, watch_cars=False)  
# Array of the final positions of cars. The function will write a similar array, at every time step, to a compresssed file and these can be extracted at any point. 

Generate_Heatmap(Road1, Time)
Generate_Heatmap(Road2, Time)


