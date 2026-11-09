1

   Abaqus 2023                                  Date 09-Nov-2026   Time 14:52:13
   For use by Supplied by Team-SolidSQUAD under license from Dassault Systemes or its subsidiary.

 CSDM_cph exact design target pressure nonlinear check                           
                                                                                 
 STEP    1     INCREMENT     1     STEP TIME    0.00    


                        S T E P       1     S T A T I C   A N A L Y S I S


                                                                                          

     AUTOMATIC TIME CONTROL WITH -
          A SUGGESTED INITIAL TIME INCREMENT OF                5.000E-02
          AND A TOTAL TIME PERIOD OF                            1.00    
          THE MINIMUM TIME INCREMENT ALLOWED IS                1.000E-08
          THE MAXIMUM TIME INCREMENT ALLOWED IS                0.100    

     LINEAR EQUATION SOLVER TYPE         DIRECT SPARSE

 CONVERGENCE TOLERANCE PARAMETERS FOR FORCE    
     CRITERION FOR RESIDUAL FORCE     FOR A NONLINEAR PROBLEM          5.000E-03
     CRITERION FOR DISP.    CORRECTION IN A NONLINEAR PROBLEM          1.000E-02
     INITIAL VALUE OF TIME AVERAGE FORCE                               1.000E-02
     AVERAGE FORCE     IS TIME AVERAGE FORCE    
     ALTERNATE CRIT. FOR RESIDUAL FORCE     FOR A NONLINEAR PROBLEM    2.000E-02
     CRITERION FOR ZERO FORCE     RELATIVE TO TIME AVRG. FORCE         1.000E-05
     CRITERION FOR RESIDUAL FORCE     WHEN THERE IS ZERO FLUX          1.000E-05
     CRITERION FOR DISP.    CORRECTION WHEN THERE IS ZERO FLUX         1.000E-03
     CRITERION FOR RESIDUAL FORCE     FOR A LINEAR INCREMENT           1.000E-08
     FIELD CONVERSION RATIO                                             1.00    
     CRITERION FOR ZERO FORCE     REL. TO TIME AVRG. MAX. FORCE        1.000E-05
     CRITERION FOR ZERO DISP.    RELATIVE TO CHARACTERISTIC LENGTH     1.000E-08

 CONVERGENCE TOLERANCE PARAMETERS FOR MOMENT   
     CRITERION FOR RESIDUAL MOMENT    FOR A NONLINEAR PROBLEM          5.000E-03
     CRITERION FOR ROTATION CORRECTION IN A NONLINEAR PROBLEM          1.000E-02
     INITIAL VALUE OF TIME AVERAGE MOMENT                              1.000E-02
     AVERAGE MOMENT    IS TIME AVERAGE MOMENT   
     ALTERNATE CRIT. FOR RESIDUAL MOMENT    FOR A NONLINEAR PROBLEM    2.000E-02
     CRITERION FOR ZERO MOMENT    RELATIVE TO TIME AVRG. MOMENT        1.000E-05
     CRITERION FOR RESIDUAL MOMENT    WHEN THERE IS ZERO FLUX          1.000E-05
     CRITERION FOR ROTATION CORRECTION WHEN THERE IS ZERO FLUX         1.000E-03
     CRITERION FOR RESIDUAL MOMENT    FOR A LINEAR INCREMENT           1.000E-08
     FIELD CONVERSION RATIO                                             1.00    
     CRITERION FOR ZERO MOMENT    REL. TO TIME AVRG. MAX. MOMENT       1.000E-05

     VOLUMETRIC STRAIN COMPATIBILITY TOLERANCE FOR HYBRID SOLIDS       1.000E-05
     AXIAL STRAIN COMPATIBILITY TOLERANCE FOR HYBRID BEAMS             1.000E-05
     TRANS. SHEAR STRAIN COMPATIBILITY TOLERANCE FOR HYBRID BEAMS      1.000E-05
     SOFT CONTACT CONSTRAINT COMPATIBILITY TOLERANCE FOR P>P0          5.000E-03
     SOFT CONTACT CONSTRAINT COMPATIBILITY TOLERANCE FOR P=0.0         0.100    
     CONTACT FORCE ERROR TOLERANCE FOR CONVERT SDI=YES                 1.00    
     DISPLACEMENT COMPATIBILITY TOLERANCE FOR DCOUP ELEMENTS           1.000E-05
     ROTATION COMPATIBILITY TOLERANCE FOR DCOUP ELEMENTS               1.000E-05

 EQUILIBRIUM WILL BE CHECKED FOR SEVERE DISCONTINUITY ITERATIONS

 TIME INCREMENTATION CONTROL PARAMETERS:
     FIRST EQUILIBRIUM ITERATION FOR CONSECUTIVE DIVERGENCE CHECK              4
     EQUILIBRIUM ITERATION AT WHICH LOG. CONVERGENCE RATE CHECK BEGINS         8
     EQUILIBRIUM ITERATION AFTER WHICH ALTERNATE RESIDUAL IS USED              9
     MAXIMUM EQUILIBRIUM ITERATIONS ALLOWED                                   16
     EQUILIBRIUM ITERATION COUNT FOR CUT-BACK IN NEXT INCREMENT               10
     MAXIMUM EQUILIB. ITERS IN TWO INCREMENTS FOR TIME INCREMENT INCREASE      4
     MAXIMUM ITERATIONS FOR SEVERE DISCONTINUITIES                            50
     MAXIMUM ATTEMPTS ALLOWED IN AN INCREMENT                                  5
     MAXIMUM DISCON. ITERS IN TWO INCREMENTS FOR TIME INCREMENT INCREASE      50
     MAXIMUM CONTACT AUGMENTATIONS FOR *SURFACE BEHAVIOR,AUGMENTED LAGRANGE   50
     CUT-BACK FACTOR AFTER DIVERGENCE                                 0.2500    
     CUT-BACK FACTOR FOR TOO SLOW CONVERGENCE                         0.5000    
     CUT-BACK FACTOR AFTER TOO MANY EQUILIBRIUM ITERATIONS            0.7500    
     CUT-BACK FACTOR AFTER TOO MANY SEVERE DISCONTINUITY ITERATIONS   0.2500    
     CUT-BACK FACTOR AFTER PROBLEMS IN ELEMENT ASSEMBLY               0.2500    
     INCREASE FACTOR AFTER TWO INCREMENTS THAT CONVERGE QUICKLY        1.500    
     MAX. TIME INCREMENT INCREASE FACTOR ALLOWED                       1.500    
     MAX. TIME INCREMENT INCREASE FACTOR ALLOWED (DYNAMICS)            1.250    
     MAX. TIME INCREMENT INCREASE FACTOR ALLOWED (DIFFUSION)           2.000    
     MINIMUM TIME INCREMENT RATIO FOR EXTRAPOLATION TO OCCUR          0.1000    
     MAX. RATIO OF TIME INCREMENT TO STABILITY LIMIT                   1.000    
     FRACTION OF STABILITY LIMIT FOR NEW TIME INCREMENT               0.9500    
     TIME INCREMENT INCREASE FACTOR BEFORE A TIME POINT                1.000    
     GLOBAL STABILIZATION CONTROL IS NOT USED

          PRINT OF INCREMENT NUMBER, TIME, ETC., EVERY    1  INCREMENTS

     THE MAXIMUM NUMBER OF INCREMENTS IN THIS STEP IS                     200

          LARGE DISPLACEMENT THEORY WILL BE USED

     LINEAR EXTRAPOLATION WILL BE USED

     CHARACTERISTIC ELEMENT LENGTH      16.7    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     COLLECTING MODEL CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

 ***WARNING: The 3-direction at one or more points in one or more layers in 690 
             elements as defined in *ORIENTATION are in the opposite direction 
             to the element normals. Either the 1 or 2 and the 3-direction 
             defined in *ORIENTATION will be reversed. The elements have been 
             identified in element set WarnElem3DirOppElemNormalStep1Inc1.


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  5.000E-02
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       26.7       TIME AVG. FORCE        26.7    
 LARGEST RESIDUAL FORCE            -0.138       AT NODE         62   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.682E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -8.682E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                      79.4       TIME AVG. MOMENT       79.4    
 LARGEST RESIDUAL MOMENT           -0.154       AT NODE         46   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.069E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.069E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       26.7       TIME AVG. FORCE        26.7    
 LARGEST RESIDUAL FORCE             7.984E-07   AT NODE       1331   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.688E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -8.151E-06   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      79.4       TIME AVG. MOMENT       79.4    
 LARGEST RESIDUAL MOMENT            9.378E-05   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.069E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.154E-07   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  5.000E-02,  FRACTION OF STEP COMPLETED  5.000E-02
 STEP TIME COMPLETED       5.000E-02,  TOTAL TIME COMPLETED        5.000E-02


  INCREMENT     2 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  5.000E-02
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       101.       TIME AVG. FORCE        63.9    
 LARGEST RESIDUAL FORCE            -9.316E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.703E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.118E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      159.       TIME AVG. MOMENT       119.    
 LARGEST RESIDUAL MOMENT            3.365E-04   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.069E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.935E-07   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          TIME INCREMENT MAY NOW INCREASE TO    7.500E-02

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  5.000E-02,  FRACTION OF STEP COMPLETED  0.100    
 STEP TIME COMPLETED       0.100    ,  TOTAL TIME COMPLETED        0.100    


  INCREMENT     3 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  7.500E-02
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       176.       TIME AVG. FORCE        101.    
 LARGEST RESIDUAL FORCE            -2.658E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -1.308E-02   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -4.026E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      279.       TIME AVG. MOMENT       172.    
 LARGEST RESIDUAL MOMENT            1.047E-03   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.360E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.583E-07   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          TIME INCREMENT MAY NOW INCREASE TO    0.100    

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  7.500E-02,  FRACTION OF STEP COMPLETED  0.175    
 STEP TIME COMPLETED       0.175    ,  TOTAL TIME COMPLETED        0.175    


  INCREMENT     4 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       275.       TIME AVG. FORCE        145.    
 LARGEST RESIDUAL FORCE            -6.724E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -1.750E-02   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -7.632E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      439.       TIME AVG. MOMENT       239.    
 LARGEST RESIDUAL MOMENT            2.920E-03   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.814E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.060E-06   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.275    
 STEP TIME COMPLETED       0.275    ,  TOTAL TIME COMPLETED        0.275    


  INCREMENT     5 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       376.       TIME AVG. FORCE        191.    
 LARGEST RESIDUAL FORCE            -7.889E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -1.756E-02   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -8.938E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      600.       TIME AVG. MOMENT       311.    
 LARGEST RESIDUAL MOMENT            4.198E-03   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.814E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.244E-06   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.375    
 STEP TIME COMPLETED       0.375    ,  TOTAL TIME COMPLETED        0.375    


  INCREMENT     6 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =  0.10000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.20000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       476.       TIME AVG. FORCE        239.    
 LARGEST RESIDUAL FORCE            -8.066E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -1.763E-02   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.122E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      761.       TIME AVG. MOMENT       386.    
 LARGEST RESIDUAL MOMENT            5.066E-03   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.814E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.272E-06   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.475    
 STEP TIME COMPLETED       0.475    ,  TOTAL TIME COMPLETED        0.475    


  INCREMENT     7 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       577.       TIME AVG. FORCE        287.    
 LARGEST RESIDUAL FORCE            -8.256E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -1.769E-02   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.318E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      923.       TIME AVG. MOMENT       463.    
 LARGEST RESIDUAL MOMENT           -5.950E-03   AT NODE         53   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.814E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.302E-06   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.575    
 STEP TIME COMPLETED       0.575    ,  TOTAL TIME COMPLETED        0.575    


  INCREMENT     8 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       678.       TIME AVG. FORCE        336.    
 LARGEST RESIDUAL FORCE            -8.459E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -1.776E-02   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.527E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.086E+03   TIME AVG. MOMENT       541.    
 LARGEST RESIDUAL MOMENT           -6.851E-03   AT NODE         53   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.814E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.333E-06   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.675    
 STEP TIME COMPLETED       0.675    ,  TOTAL TIME COMPLETED        0.675    


  INCREMENT     9 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       779.       TIME AVG. FORCE        385.    
 LARGEST RESIDUAL FORCE            -8.669E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -1.783E-02   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.743E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.249E+03   TIME AVG. MOMENT       619.    
 LARGEST RESIDUAL MOMENT           -7.768E-03   AT NODE         53   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.815E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.366E-06   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.775    
 STEP TIME COMPLETED       0.775    ,  TOTAL TIME COMPLETED        0.775    


  INCREMENT    10 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =  0.10000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.20000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       878.       TIME AVG. FORCE        434.    
 LARGEST RESIDUAL FORCE            -8.886E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -1.790E-02   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.967E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.413E+03   TIME AVG. MOMENT       699.    
 LARGEST RESIDUAL MOMENT           -8.703E-03   AT NODE         53   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.815E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.400E-06   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.875    
 STEP TIME COMPLETED       0.875    ,  TOTAL TIME COMPLETED        0.875    


  INCREMENT    11 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  0.100    
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       977.       TIME AVG. FORCE        484.    
 LARGEST RESIDUAL FORCE            -9.111E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.798E-02   AT NODE        694   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.020E-04   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.578E+03   TIME AVG. MOMENT       779.    
 LARGEST RESIDUAL MOMENT           -9.655E-03   AT NODE         53   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.815E-04   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.434E-06   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  0.100    ,  FRACTION OF STEP COMPLETED  0.975    
 STEP TIME COMPLETED       0.975    ,  TOTAL TIME COMPLETED        0.975    


  INCREMENT    12 STARTS. ATTEMPT NUMBER  1, TIME INCREMENT  2.500E-02
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8370
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         2.984e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.006E+03   TIME AVG. FORCE        527.    
 LARGEST RESIDUAL FORCE            -3.861E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         4.508E-03   AT NODE        694   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.691E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.619E+03   TIME AVG. MOMENT       849.    
 LARGEST RESIDUAL MOMENT           -1.448E-03   AT NODE         53   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.538E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.391E-07   AT NODE        720   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   1 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  1 ARE EQUILIBRIUM ITERATIONS.

 TIME INCREMENT COMPLETED  2.500E-02,  FRACTION OF STEP COMPLETED   1.00    
 STEP TIME COMPLETED        1.00    ,  TOTAL TIME COMPLETED         1.00    


          THE ANALYSIS HAS BEEN COMPLETED



     ANALYSIS SUMMARY:
     TOTAL OF         12  INCREMENTS
                       0  CUTBACKS IN AUTOMATIC INCREMENTATION
                      13  ITERATIONS INCLUDING CONTACT ITERATIONS IF PRESENT
                      13  PASSES THROUGH THE EQUATION SOLVER OF WHICH 
                      13  INVOLVE MATRIX DECOMPOSITION, INCLUDING
                       0  DECOMPOSITION(S) OF THE MASS MATRIX
                       1  REORDERING OF EQUATIONS TO MINIMIZE WAVEFRONT
                       0  ADDITIONAL RESIDUAL EVALUATIONS FOR LINE SEARCHES
                       0  ADDITIONAL OPERATOR EVALUATIONS FOR LINE SEARCHES
                       2  WARNING MESSAGES DURING USER INPUT PROCESSING
                       1  WARNING MESSAGES DURING ANALYSIS
                       0  ANALYSIS WARNINGS ARE NUMERICAL PROBLEM MESSAGES
                       0  ANALYSIS WARNINGS ARE NEGATIVE EIGENVALUE MESSAGES
                       0  ERROR MESSAGES



     JOB TIME SUMMARY
       USER TIME (SEC)      =      8.0    
       SYSTEM TIME (SEC)    =      1.3    
       TOTAL CPU TIME (SEC) =      9.3    
       WALLCLOCK TIME (SEC) =            9
       MEMORY PEAK (GB)     =            0
