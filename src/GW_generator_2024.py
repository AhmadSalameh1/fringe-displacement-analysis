import sys
from random import uniform
import numba as nb
import numexpr as ne
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import *
from scipy import signal
from scipy.signal import windows

CST_G_NEWTON = 6.674e-8 #cm3.g-1.s-2
CST_C = 2.99e10 #cm.s-1
CST_M_SUN = 1.99e33 #g
CST_PC = 3.086e18 #cm

def f_t2(F0,t,tc):
    return F0/pow(1-t/tc,3./8.)
def Amplitude(Mc,t) : 
    
    global CST_G_NEWTON, CST_C
    
    amplitude = np.power(CST_G_NEWTON*Mc, 5./4.)*np.power(CST_C, -11/4)*np.power(5./t, 1./4.) 
    
    return amplitude #4*pow(Mc,5./3.)*pow(pi*f_t2(F0,t,tc),2./3.)/D

def Phase(t,Mc,phi0):
    
    phase = phi0 - 2.*np.power(np.power(CST_C,3.)*t/(5.*CST_G_NEWTON*Mc), 5./8.)
    
    return phase #10.05*F0*tc*pow(1-t/tc,5./8.)

def Polar(theta, phi, psi, itf=0):
    
    x = (np.sin(phi)*np.cos(psi)-np.sin(psi)*np.cos(phi)*np.cos(theta),
         -(np.cos(phi)*np.cos(psi)+np.sin(psi)*np.sin(phi)*np.cos(theta)),
           np.sin(psi)*np.cos(theta))
    y = (-(np.sin(phi)*np.sin(psi)+np.cos(phi)*np.cos(psi)*np.cos(theta)),
         np.cos(phi)*np.sin(psi)-np.cos(psi)*np.sin(phi)*np.cos(theta),
         np.cos(psi)*np.sin(theta))
    
    e_plus = np.array([[ (x[i]*x[j]-y[i]*y[j]) for j in range(0,3)] for i in range(0,3)])
    e_cross = np.array([[ (x[i]*y[j]+y[i]*x[j]) for j in range(0,3)] for i in range(0,3)])
    
    if itf == "H1":
        n_x = (-0.2229, 0.7998, 0.5569)
        n_y = (-0.9140, 0.0261, -0.4049)
    elif itf == "L1":
        n_x = (-0.9546, -0.1416, -0.2622)
        n_y = (0.2977, -0.4879, -0.8205)
    elif itf == "V1":
        n_x = (-0.7005, 0.2085, 0.6826)
        n_y = (-0.0538, -0.9691, 0.2408)
    else :
        n_x = (1, 0, 0)
        n_y = (0, 1, 0)
    
    d = 1./2.*np.array([[ (n_x[i]*n_x[j]-n_y[i]*n_y[j]) for j in range(0,3)] for i in range(0,3)])
    
    formFactor_plus = np.sum(d*e_plus)
    formFactor_cross = np.sum(d*e_cross)
    
    return formFactor_plus, formFactor_cross

def WaveformTD(amplitude, dist_L, phase, theta=0, phi=0, polarization=0, inclination=0, itf=None):
    
    h_plus = amplitude/dist_L*(1+np.cos(inclination)**2)/2*np.cos(phase)
    h_cross= amplitude/dist_L*np.cos(inclination)*np.sin(phase)
    
    formFactor_plus, formFactor_cross = Polar(theta, phi, polarization, itf)
    
    h = h_plus*formFactor_plus + h_cross*formFactor_cross
    
    
    return h

def TaperingWindow(F_ech, t, tc):
    
#    window = signal.hann(int(F_ech*0.1*2), sym = True)
    window = windows.hann(int(F_ech*0.1*2), sym = True)    
    
    tapering = np.ones_like(t)
    tapering[:int(F_ech*0.1)] = window[:int(F_ech*0.1)]
    tapering[-int(F_ech*0.1):] = window[-int(F_ech*0.1):]
    
    return tapering

def generation(mass1,                # Mass of the 1st companion [Msol]
               mass2,                # Mass of the 1st companion [Msol]
               distance,             # Luminosity distance to the observer [pc]
               theta=0,              # theta angle 
               phi=0,                # phi angle
               polarization=0,       # Polarization angle
               inclination=0,        # Inclination angle
               itf=None,             # Inteferometer used among H1, L1, V1
               F_ech=4096):          # sampling frequency in Hz
    #M1 et M2 en masse solaires
    #D en pc
    #F_ech en Hz

    global CST_G_NEWTON, CST_C, CST_PC, CST_M_SUN

    temp_t = []
    temp_hc = []
    F = []
    D = distance*CST_PC
    m1 = mass1*CST_M_SUN
    m2 = mass2*CST_M_SUN
    mtot = m1+m2
    eta = m1*m2/np.power(mtot,2.)
    Mc = mtot*np.power(eta,3./5.)
    phi0 = 0.
    F0= 10.
    tc = 9.23e-4*np.power(CST_C,5.)/(pow(F0,8./3.)*np.power(Mc,5./3.)*np.power(CST_G_NEWTON,5./3.))   
    
    t = np.linspace(tc, 0, int(tc)*F_ech+1)[:-1]
    tapering = TaperingWindow(F_ech, t, tc)
    
    amplitude=Amplitude(Mc, t)
    phase=Phase(t, Mc, phi0)
    waveform = WaveformTD(amplitude, D, phase, theta, phi, polarization, inclination, itf)
    
    waveform_tapered = tapering*waveform
    
    return waveform_tapered
    
    """
    i=0
    while t<=tc- 1/F_ech: 
        t+=1/F_ech
        temp_t.append(t)
        if t<0.1 : 
            tapering = window[i]
        elif (tc-t)<0.1 : 
            tapering =window[i-int(F_ech*tc)]
        else : 
            tapering = 1.
        temp = tapering*pow(G,5./3.)*Amplitude(Mc,F0,t,D,tc)*cos(phi(t,Mc,F0,tc))/pow(c,4.)
        temp_hc.append(temp)
        i+=1
    print("nombre de points : ",i," durée analytique tc (s): ",tc)
    df = pd.DataFrame(temp_hc)
    df.to_csv("template.txt", sep = ' ',index = False, header = None)
    return ( temp_hc)"""

    
    
    
    
