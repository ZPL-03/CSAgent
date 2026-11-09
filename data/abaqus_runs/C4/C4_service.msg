1

   Abaqus 2023                                  Date 09-Nov-2026   Time 14:51:43
   For use by Supplied by Team-SolidSQUAD under license from Dassault Systemes or its subsidiary.

 CSDM_cph exact service pressure nonlinear check                                 
                                                                                 
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

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       13.4       TIME AVG. FORCE        13.4    
 LARGEST RESIDUAL FORCE            -3.461E-02   AT NODE         62   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -4.341E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -4.341E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -2.159E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                      39.7       TIME AVG. MOMENT       39.7    
 LARGEST RESIDUAL MOMENT           -3.861E-02   AT NODE         46   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.535E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.535E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
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

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       13.4       TIME AVG. FORCE        13.4    
 LARGEST RESIDUAL FORCE             2.026E-07   AT NODE       1325   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -4.342E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.033E-06   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      39.7       TIME AVG. MOMENT       39.7    
 LARGEST RESIDUAL MOMENT            1.172E-05   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.535E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.878E-08   AT NODE        720   DOF  5
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


 AVERAGE FORCE                       50.6       TIME AVG. FORCE        32.0    
 LARGEST RESIDUAL FORCE            -1.161E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -4.346E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -5.275E-06   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      79.5       TIME AVG. MOMENT       59.6    
 LARGEST RESIDUAL MOMENT            4.201E-05   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.535E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -7.308E-08   AT NODE        720   DOF  5
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

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       88.1       TIME AVG. FORCE        50.7    
 LARGEST RESIDUAL FORCE            -3.286E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -6.526E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.953E-06   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      139.       TIME AVG. MOMENT       86.1    
 LARGEST RESIDUAL MOMENT            1.304E-04   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -6.802E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.379E-07   AT NODE        720   DOF  5
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

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       138.       TIME AVG. FORCE        72.5    
 LARGEST RESIDUAL FORCE            -8.245E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.714E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.872E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      219.       TIME AVG. MOMENT       119.    
 LARGEST RESIDUAL MOMENT            3.628E-04   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.069E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.596E-07   AT NODE        720   DOF  5
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

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       188.       TIME AVG. FORCE        95.5    
 LARGEST RESIDUAL FORCE            -9.554E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.730E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.167E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      299.       TIME AVG. MOMENT       155.    
 LARGEST RESIDUAL MOMENT            5.194E-04   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.070E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.009E-07   AT NODE        720   DOF  5
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
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       238.       TIME AVG. FORCE        119.    
 LARGEST RESIDUAL FORCE            -9.661E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.745E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.189E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      379.       TIME AVG. MOMENT       192.    
 LARGEST RESIDUAL MOMENT            6.244E-04   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.070E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.042E-07   AT NODE        720   DOF  5
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


 AVERAGE FORCE                       289.       TIME AVG. FORCE        144.    
 LARGEST RESIDUAL FORCE            -9.774E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.761E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.212E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      459.       TIME AVG. MOMENT       231.    
 LARGEST RESIDUAL MOMENT            7.303E-04   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.070E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.076E-07   AT NODE        720   DOF  5
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

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       339.       TIME AVG. FORCE        168.    
 LARGEST RESIDUAL FORCE            -9.895E-05   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.776E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.236E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      539.       TIME AVG. MOMENT       269.    
 LARGEST RESIDUAL MOMENT            8.371E-04   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.070E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.112E-07   AT NODE        720   DOF  5
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

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       390.       TIME AVG. FORCE        193.    
 LARGEST RESIDUAL FORCE            -1.002E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.792E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.260E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      620.       TIME AVG. MOMENT       308.    
 LARGEST RESIDUAL MOMENT            9.447E-04   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.070E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.149E-07   AT NODE        720   DOF  5
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

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       441.       TIME AVG. FORCE        217.    
 LARGEST RESIDUAL FORCE            -1.014E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.809E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.285E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      700.       TIME AVG. MOMENT       347.    
 LARGEST RESIDUAL MOMENT            1.053E-03   AT NODE       1308   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.071E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.187E-07   AT NODE        720   DOF  5
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


 AVERAGE FORCE                       491.       TIME AVG. FORCE        242.    
 LARGEST RESIDUAL FORCE            -1.026E-04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.825E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.310E-05   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      781.       TIME AVG. MOMENT       387.    
 LARGEST RESIDUAL MOMENT           -1.163E-03   AT NODE         53   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.071E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.225E-07   AT NODE        720   DOF  5
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


 AVERAGE FORCE                       505.       TIME AVG. FORCE        264.    
 LARGEST RESIDUAL FORCE            -4.210E-06   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -2.209E-03   AT NODE        712   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -3.721E-06   AT NODE        703   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      801.       TIME AVG. MOMENT       421.    
 LARGEST RESIDUAL MOMENT           -1.720E-04   AT NODE         53   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.268E-05   AT NODE         80   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.214E-08   AT NODE        720   DOF  5
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
       USER TIME (SEC)      =      6.9    
       SYSTEM TIME (SEC)    =     0.70    
       TOTAL CPU TIME (SEC) =      7.6    
       WALLCLOCK TIME (SEC) =            8
       MEMORY PEAK (GB)     =            0
