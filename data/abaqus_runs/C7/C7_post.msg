1

   Abaqus 2023                                  Date 09-Nov-2026   Time 20:12:37
   For use by Supplied by Team-SolidSQUAD under license from Dassault Systemes or its subsidiary.

 CSDM_cph pressure hull first-mode imperfection Riks postbuckling                
                                                                                 
 STEP    1     INCREMENT     1     STEP TIME    0.00    


                        S T E P       1     S T A T I C   A N A L Y S I S


                                                                                          

     AUTOMATIC LOAD CONTROL WITH -
          A SUGGESTED INITIAL INCREMENT IN ARC LENGTH           1.000E-02
          AND A TOTAL ARC LENGTH SCALE FACTOR OF                 1.00    
          THE MINIMUM ARC LENGTH INCREMENT ALLOWED IS           1.000E-10
          THE MAXIMUM ARC LENGTH INCREMENT ALLOWED IS           0.100    

     LINEAR EQUATION SOLVER TYPE         DIRECT SPARSE

     MODIFIED RIKS METHOD IS USED - AMPLITUDE REFERENCES ARE IGNORED

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

     THE MAXIMUM NUMBER OF INCREMENTS IN THIS STEP IS                     300

          LARGE DISPLACEMENT THEORY WILL BE USED

     LINEAR EXTRAPOLATION WILL BE USED

     CHARACTERISTIC ELEMENT LENGTH      18.4    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     COLLECTING MODEL CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

 ***WARNING: The 3-direction at one or more points in one or more layers in 570 
             elements as defined in *ORIENTATION are in the opposite direction 
             to the element normals. Either the 1 or 2 and the 3-direction 
             defined in *ORIENTATION will be reversed. The elements have been 
             identified in element set WarnElem3DirOppElemNormalStep1Inc1.


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       60.1       TIME AVG. FORCE        60.1    
 LARGEST RESIDUAL FORCE            -0.669       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.565E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.565E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                      166.       TIME AVG. MOMENT       166.    
 LARGEST RESIDUAL MOMENT            0.684       AT NODE         56   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.724E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.724E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       60.0       TIME AVG. FORCE        60.0    
 LARGEST RESIDUAL FORCE            -3.768E-06   AT NODE       1082   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.567E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -3.845E-05   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      167.       TIME AVG. MOMENT       167.    
 LARGEST RESIDUAL MOMENT            5.457E-04   AT NODE       1076   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.724E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.161E-07   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     1 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         9.9954E-03
     TOTAL ARC LENGTH   1.000E-02, INCREMENT OF ARC LENGTH   1.000E-02


  INCREMENT     2 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       228.       TIME AVG. FORCE        144.    
 LARGEST RESIDUAL FORCE            -0.657       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.570E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.570E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    2.805E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                      334.       TIME AVG. MOMENT       250.    
 LARGEST RESIDUAL MOMENT            0.837       AT NODE       1074   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.723E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.723E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       228.       TIME AVG. FORCE        144.    
 LARGEST RESIDUAL FORCE             6.863E-06   AT NODE         74   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.572E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -3.835E-05   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      334.       TIME AVG. MOMENT       250.    
 LARGEST RESIDUAL MOMENT            7.825E-04   AT NODE       1076   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.722E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.097E-07   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    1.500E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     2 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         1.9980E-02
     TOTAL ARC LENGTH   2.000E-02, INCREMENT OF ARC LENGTH   1.000E-02


  INCREMENT     3 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       397.       TIME AVG. FORCE        228.    
 LARGEST RESIDUAL FORCE             -1.48       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         2.364E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.364E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                      586.       TIME AVG. MOMENT       362.    
 LARGEST RESIDUAL MOMENT             2.00       AT NODE       1074   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.581E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.581E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       397.       TIME AVG. FORCE        228.    
 LARGEST RESIDUAL FORCE             2.717E-05   AT NODE       1101   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         2.368E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -8.843E-05   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      587.       TIME AVG. MOMENT       363.    
 LARGEST RESIDUAL MOMENT            2.900E-03   AT NODE       1076   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.579E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.170E-06   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    2.250E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     3 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         3.4934E-02
     TOTAL ARC LENGTH   3.500E-02, INCREMENT OF ARC LENGTH   1.500E-02


  INCREMENT     4 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       647.       TIME AVG. FORCE        333.    
 LARGEST RESIDUAL FORCE             -3.32       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         3.565E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.565E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                      968.       TIME AVG. MOMENT       514.    
 LARGEST RESIDUAL MOMENT             4.68       AT NODE       1074   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.864E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.864E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       647.       TIME AVG. FORCE        333.    
 LARGEST RESIDUAL FORCE             1.027E-04   AT NODE       1101   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         3.576E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.073E-04   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      969.       TIME AVG. MOMENT       514.    
 LARGEST RESIDUAL MOMENT            1.027E-02   AT NODE       1076   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.859E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.727E-06   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    3.375E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     4 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         5.7310E-02
     TOTAL ARC LENGTH   5.750E-02, INCREMENT OF ARC LENGTH   2.250E-02


  INCREMENT     5 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.015E+03   TIME AVG. FORCE        469.    
 LARGEST RESIDUAL FORCE             -7.45       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         5.394E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        5.394E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.547E+03   TIME AVG. MOMENT       721.    
 LARGEST RESIDUAL MOMENT             10.7       AT NODE       1074   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -5.777E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.777E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.014E+03   TIME AVG. FORCE        469.    
 LARGEST RESIDUAL FORCE             3.817E-04   AT NODE       1101   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         5.419E-02   AT NODE        567   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -4.976E-04   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.551E+03   TIME AVG. MOMENT       721.    
 LARGEST RESIDUAL MOMENT            3.520E-02   AT NODE       1076   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -5.764E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -6.495E-06   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -5.168E-06
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    5.063E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     5 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         9.0734E-02
     TOTAL ARC LENGTH   9.125E-02, INCREMENT OF ARC LENGTH   3.375E-02


  INCREMENT     6 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.565E+03   TIME AVG. FORCE        652.    
 LARGEST RESIDUAL FORCE             -16.6       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.202E-02   AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -8.202E-02   AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.435E+03   TIME AVG. MOMENT      1.007E+03
 LARGEST RESIDUAL MOMENT            -24.4       AT NODE         45   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.617E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.617E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.562E+03   TIME AVG. FORCE        651.    
 LARGEST RESIDUAL FORCE             1.419E-03   AT NODE       1101   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.267E-02   AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.235E-03   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    1.052E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.443E+03   TIME AVG. MOMENT      1.008E+03
 LARGEST RESIDUAL MOMENT            0.117       AT NODE       1079   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.583E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.594E-05   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      1.562E+03   TIME AVG. FORCE        651.    
 LARGEST RESIDUAL FORCE             5.208E-07   AT NODE         57   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -8.267E-02   AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.790E-08   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.443E+03   TIME AVG. MOMENT      1.008E+03
 LARGEST RESIDUAL MOMENT            2.223E-05   AT NODE         72   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.583E-04   AT NODE       1109   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     7.334E-09   AT NODE        111   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    7.594E-02

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     6 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.1405    
     TOTAL ARC LENGTH   0.142    , INCREMENT OF ARC LENGTH   5.063E-02


  INCREMENT     7 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.369E+03   TIME AVG. FORCE        897.    
 LARGEST RESIDUAL FORCE             -36.8       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.126       AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.126       AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.813E+03   TIME AVG. MOMENT      1.409E+03
 LARGEST RESIDUAL MOMENT            -54.4       AT NODE         45   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.279E-03   AT NODE         66   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.279E-03   AT NODE         66   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.362E+03   TIME AVG. FORCE        896.    
 LARGEST RESIDUAL FORCE            -7.248E-03   AT NODE        590   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.127       AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -3.209E-03   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -6.314E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     3.835E+03   TIME AVG. MOMENT      1.412E+03
 LARGEST RESIDUAL MOMENT            0.366       AT NODE       1079   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.270E-03   AT NODE         66   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.067E-05   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      2.362E+03   TIME AVG. FORCE        896.    
 LARGEST RESIDUAL FORCE            -5.449E-06   AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.127       AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.555E-07   AT NODE        559   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.835E+03   TIME AVG. MOMENT      1.412E+03
 LARGEST RESIDUAL MOMENT            1.247E-04   AT NODE       1100   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.270E-03   AT NODE         66   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.136E-08   AT NODE       1045   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    0.100    

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     7 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.2140    
     TOTAL ARC LENGTH   0.218    , INCREMENT OF ARC LENGTH   7.594E-02


  INCREMENT     8 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.400E+03   TIME AVG. FORCE       1.209E+03
 LARGEST RESIDUAL FORCE             -61.5       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.172       AT NODE        586   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.172       AT NODE        586   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     5.740E+03   TIME AVG. MOMENT      1.953E+03
 LARGEST RESIDUAL MOMENT            -96.0       AT NODE       1093   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.650E-03   AT NODE         66   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.650E-03   AT NODE         66   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.383E+03   TIME AVG. FORCE       1.207E+03
 LARGEST RESIDUAL FORCE            -3.048E-02   AT NODE        576   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.175       AT NODE        586   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -6.695E-03   AT NODE        560   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -3.318E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     5.787E+03   TIME AVG. MOMENT      1.959E+03
 LARGEST RESIDUAL MOMENT            -1.05       AT NODE         52   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.628E-03   AT NODE       1090   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.200E-05   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.383E+03   TIME AVG. FORCE       1.207E+03
 LARGEST RESIDUAL FORCE             4.069E-05   AT NODE       1087   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.175       AT NODE        586   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -3.426E-06   AT NODE        559   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     5.787E+03   TIME AVG. MOMENT      1.959E+03
 LARGEST RESIDUAL MOMENT           -1.067E-03   AT NODE       1088   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.628E-03   AT NODE       1090   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.042E-07   AT NODE         93   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     8 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.3077    
     TOTAL ARC LENGTH   0.318    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT     9 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.370E+03   TIME AVG. FORCE       1.558E+03
 LARGEST RESIDUAL FORCE             -56.8       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.180       AT NODE        570   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.180       AT NODE        570   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     7.841E+03   TIME AVG. MOMENT      2.613E+03
 LARGEST RESIDUAL MOMENT             105.       AT NODE         63   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.587E-03   AT NODE       1090   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.587E-03   AT NODE       1090   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.346E+03   TIME AVG. FORCE       1.556E+03
 LARGEST RESIDUAL FORCE            -3.673E-02   AT NODE        576   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.183       AT NODE        570   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        7.885E-03   AT NODE        559   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    5.095E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     7.892E+03   TIME AVG. MOMENT      2.618E+03
 LARGEST RESIDUAL MOMENT            -1.99       AT NODE         52   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.556E-03   AT NODE         48   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.107E-05   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      4.346E+03   TIME AVG. FORCE       1.556E+03
 LARGEST RESIDUAL FORCE             8.686E-05   AT NODE       1087   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.183       AT NODE        570   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -3.077E-06   AT NODE        559   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     7.892E+03   TIME AVG. MOMENT      2.618E+03
 LARGEST RESIDUAL MOMENT            1.496E-03   AT NODE         68   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.556E-03   AT NODE         48   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.640E-07   AT NODE         93   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     9 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.3963    
     TOTAL ARC LENGTH   0.418    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    10 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.259E+03   TIME AVG. FORCE       1.926E+03
 LARGEST RESIDUAL FORCE             -49.9       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.188       AT NODE        570   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.188       AT NODE        570   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.011E+04   TIME AVG. MOMENT      3.368E+03
 LARGEST RESIDUAL MOMENT            -111.       AT NODE         44   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.654E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.654E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.228E+03   TIME AVG. FORCE       1.923E+03
 LARGEST RESIDUAL FORCE             5.029E-02   AT NODE       1059   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.192       AT NODE        568   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.590E-03   AT NODE        559   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -8.658E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.016E+04   TIME AVG. MOMENT      3.373E+03
 LARGEST RESIDUAL MOMENT             3.08       AT NODE       1104   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.746E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.212E-05   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      5.228E+03   TIME AVG. FORCE       1.923E+03
 LARGEST RESIDUAL FORCE             1.311E-04   AT NODE       1087   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.192       AT NODE        568   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.386E-06   AT NODE        894   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.016E+04   TIME AVG. MOMENT      3.373E+03
 LARGEST RESIDUAL MOMENT            1.865E-03   AT NODE       1100   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.746E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.218E-07   AT NODE       1045   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    10 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4776    
     TOTAL ARC LENGTH   0.518    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    11 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      6.043E+03   TIME AVG. FORCE       2.297E+03
 LARGEST RESIDUAL FORCE             -41.1       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.196       AT NODE        568   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.196       AT NODE        568   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.255E+04   TIME AVG. MOMENT      4.206E+03
 LARGEST RESIDUAL MOMENT            -112.       AT NODE       1094   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.908E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.908E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      6.007E+03   TIME AVG. FORCE       2.294E+03
 LARGEST RESIDUAL FORCE             6.372E-02   AT NODE       1059   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.198       AT NODE        568   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.419E-03   AT NODE        579   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.305E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.259E+04   TIME AVG. MOMENT      4.210E+03
 LARGEST RESIDUAL MOMENT             3.95       AT NODE         71   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.990E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.227E-05   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      6.007E+03   TIME AVG. FORCE       2.294E+03
 LARGEST RESIDUAL FORCE             1.190E-04   AT NODE       1087   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.198       AT NODE        568   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.080E-05   AT NODE        579   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.259E+04   TIME AVG. MOMENT      4.210E+03
 LARGEST RESIDUAL MOMENT           -5.525E-03   AT NODE         53   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.990E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     2.587E-07   AT NODE        111   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    11 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.5499    
     TOTAL ARC LENGTH   0.618    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    12 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      6.715E+03   TIME AVG. FORCE       2.662E+03
 LARGEST RESIDUAL FORCE              364.       AT NODE         51   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.200       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.200       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.510E+04   TIME AVG. MOMENT      5.117E+03
 LARGEST RESIDUAL MOMENT           -2.439E+03   AT NODE         51   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.132E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.132E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      6.676E+03   TIME AVG. FORCE       2.659E+03
 LARGEST RESIDUAL FORCE             0.107       AT NODE       1087   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.201       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        7.840E-03   AT NODE        579   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    2.309E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.513E+04   TIME AVG. MOMENT      5.120E+03
 LARGEST RESIDUAL MOMENT            -9.28       AT NODE         51   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.200E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     6.914E-05   AT NODE         63   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.631E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    12 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.6120    
     TOTAL ARC LENGTH   0.718    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    13 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      7.273E+03   TIME AVG. FORCE       3.014E+03
 LARGEST RESIDUAL FORCE             -580.       AT NODE       1104   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.202       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.202       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.773E+04   TIME AVG. MOMENT      6.090E+03
 LARGEST RESIDUAL MOMENT            4.177E+03   AT NODE       1104   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.308E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.308E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      7.233E+03   TIME AVG. FORCE       3.011E+03
 LARGEST RESIDUAL FORCE             0.197       AT NODE       1105   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.202       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -6.919E-03   AT NODE        577   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    2.356E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.776E+04   TIME AVG. MOMENT      6.092E+03
 LARGEST RESIDUAL MOMENT             15.9       AT NODE       1104   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.358E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.312E-04   AT NODE       1104   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    4.994E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    13 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.6640    
     TOTAL ARC LENGTH   0.818    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    14 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      7.732E+03   TIME AVG. FORCE       3.348E+03
 LARGEST RESIDUAL FORCE              413.       AT NODE         72   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.202       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.202       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.042E+04   TIME AVG. MOMENT      7.116E+03
 LARGEST RESIDUAL MOMENT            3.275E+03   AT NODE         72   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.433E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.433E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      7.701E+03   TIME AVG. FORCE       3.346E+03
 LARGEST RESIDUAL FORCE            -0.117       AT NODE         71   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.201       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        4.900E-03   AT NODE        580   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.384E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.044E+04   TIME AVG. MOMENT      7.117E+03
 LARGEST RESIDUAL MOMENT             11.5       AT NODE         72   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.465E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.066E-04   AT NODE         72   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    3.731E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    14 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.7077    
     TOTAL ARC LENGTH   0.918    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    15 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      7.775E+03   TIME AVG. FORCE       3.641E+03
 LARGEST RESIDUAL FORCE            -2.569E+04   AT NODE        558   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.205       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.205       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.936E+04   TIME AVG. MOMENT      7.933E+03
 LARGEST RESIDUAL MOMENT            2.464E+05   AT NODE        580   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.713E-03   AT NODE        574   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.713E-03   AT NODE        574   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.866E+03   TIME AVG. FORCE       3.514E+03
 LARGEST RESIDUAL FORCE              336.       AT NODE        562   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.448       AT NODE        578   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.300       AT NODE        578   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.667E+04   TIME AVG. MOMENT      7.753E+03
 LARGEST RESIDUAL MOMENT             509.       AT NODE        556   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.171E-02   AT NODE        558   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.637E-03   AT NODE        558   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      5.904E+03   TIME AVG. FORCE       3.517E+03
 LARGEST RESIDUAL FORCE             -1.17       AT NODE        581   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.437       AT NODE        578   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.042E-02   AT NODE        578   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -3.624E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.669E+04   TIME AVG. MOMENT      7.755E+03
 LARGEST RESIDUAL MOMENT             32.4       AT NODE        558   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.162E-02   AT NODE        558   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.221E-04   AT NODE        580   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -7.773E-06
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    15 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.5376    
     TOTAL ARC LENGTH    1.02    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    16 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      6.115E+03   TIME AVG. FORCE       3.679E+03
 LARGEST RESIDUAL FORCE            -1.964E+04   AT NODE        431   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.219       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.219       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.751E+04   TIME AVG. MOMENT      8.365E+03
 LARGEST RESIDUAL MOMENT            1.598E+05   AT NODE        431   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.720E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.720E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.372E+03   TIME AVG. FORCE       3.633E+03
 LARGEST RESIDUAL FORCE              62.7       AT NODE        650   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.266       AT NODE        560   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.123       AT NODE        560   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.650E+04   TIME AVG. MOMENT      8.302E+03
 LARGEST RESIDUAL MOMENT            -496.       AT NODE        431   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      7.094E-03   AT NODE        431   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     5.665E-03   AT NODE        431   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      5.377E+03   TIME AVG. FORCE       3.633E+03
 LARGEST RESIDUAL FORCE            -0.167       AT NODE        644   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.264       AT NODE        560   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.254E-03   AT NODE        558   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.650E+04   TIME AVG. MOMENT      8.302E+03
 LARGEST RESIDUAL MOMENT             3.79       AT NODE        577   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      7.082E-03   AT NODE        431   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.706E-05   AT NODE        355   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    16 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4868    
     TOTAL ARC LENGTH    1.12    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    17 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.590E+03   TIME AVG. FORCE       3.748E+03
 LARGEST RESIDUAL FORCE            -1.534E+04   AT NODE        374   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.222       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.222       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.786E+04   TIME AVG. MOMENT      8.864E+03
 LARGEST RESIDUAL MOMENT           -1.196E+05   AT NODE        744   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.765E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.765E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.276E+03   TIME AVG. FORCE       3.730E+03
 LARGEST RESIDUAL FORCE             -18.8       AT NODE        745   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.262       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        5.963E-02   AT NODE        375   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.752E+04   TIME AVG. MOMENT      8.844E+03
 LARGEST RESIDUAL MOMENT             842.       AT NODE        744   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.788E-03   AT NODE        374   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.758E-03   AT NODE        374   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      5.277E+03   TIME AVG. FORCE       3.730E+03
 LARGEST RESIDUAL FORCE             6.014E-02   AT NODE        744   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.262       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -5.315E-04   AT NODE        745   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.752E+04   TIME AVG. MOMENT      8.844E+03
 LARGEST RESIDUAL MOMENT             2.94       AT NODE        338   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.767E-03   AT NODE        374   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     3.323E-05   AT NODE        337   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    17 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4749    
     TOTAL ARC LENGTH    1.22    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    18 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.468E+03   TIME AVG. FORCE       3.826E+03
 LARGEST RESIDUAL FORCE            -1.506E+04   AT NODE        764   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.223       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.223       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.898E+04   TIME AVG. MOMENT      9.407E+03
 LARGEST RESIDUAL MOMENT            1.176E+05   AT NODE        764   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.800E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.800E-03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.270E+03   TIME AVG. FORCE       3.815E+03
 LARGEST RESIDUAL FORCE             -15.5       AT NODE        763   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.245       AT NODE        551   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -4.308E-02   AT NODE        374   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -4.436E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.871E+04   TIME AVG. MOMENT      9.392E+03
 LARGEST RESIDUAL MOMENT             785.       AT NODE        744   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      5.425E-03   AT NODE        764   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     4.122E-03   AT NODE        764   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      5.270E+03   TIME AVG. FORCE       3.815E+03
 LARGEST RESIDUAL FORCE             7.877E-02   AT NODE        838   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.245       AT NODE        551   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.442E-04   AT NODE        374   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.871E+04   TIME AVG. MOMENT      9.393E+03
 LARGEST RESIDUAL MOMENT             3.09       AT NODE        800   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      5.406E-03   AT NODE        764   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     3.369E-05   AT NODE        337   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    18 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4727    
     TOTAL ARC LENGTH    1.32    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    19 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.428E+03   TIME AVG. FORCE       3.900E+03
 LARGEST RESIDUAL FORCE             1.453E+04   AT NODE        589   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.231       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.231       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.000E+04   TIME AVG. MOMENT      9.951E+03
 LARGEST RESIDUAL MOMENT           -6.550E+04   AT NODE        762   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.918E-03   AT NODE        591   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.918E-03   AT NODE        591   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.193E+03   TIME AVG. FORCE       3.888E+03
 LARGEST RESIDUAL FORCE              82.6       AT NODE        589   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.351       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.120       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.008E+04   TIME AVG. MOMENT      9.955E+03
 LARGEST RESIDUAL MOMENT             417.       AT NODE        744   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -7.570E-03   AT NODE        589   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.950E-03   AT NODE        607   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      5.193E+03   TIME AVG. FORCE       3.888E+03
 LARGEST RESIDUAL FORCE             7.357E-02   AT NODE        680   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.351       AT NODE        587   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.091E-04   AT NODE        546   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.008E+04   TIME AVG. MOMENT      9.955E+03
 LARGEST RESIDUAL MOMENT             2.80       AT NODE        589   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -7.567E-03   AT NODE        589   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.441E-05   AT NODE        532   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    19 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4636    
     TOTAL ARC LENGTH    1.42    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    20 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.323E+03   TIME AVG. FORCE       3.959E+03
 LARGEST RESIDUAL FORCE             1.458E+04   AT NODE        782   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.240       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.240       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.117E+04   TIME AVG. MOMENT      1.052E+04
 LARGEST RESIDUAL MOMENT            1.452E+05   AT NODE        782   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.140E-03   AT NODE        590   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.140E-03   AT NODE        590   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.056E+03   TIME AVG. FORCE       3.946E+03
 LARGEST RESIDUAL FORCE              69.1       AT NODE        590   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.358       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.119       AT NODE        514   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.130E+04   TIME AVG. MOMENT      1.052E+04
 LARGEST RESIDUAL MOMENT            -955.       AT NODE        782   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.069E-03   AT NODE        514   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -6.425E-03   AT NODE        514   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      5.057E+03   TIME AVG. FORCE       3.946E+03
 LARGEST RESIDUAL FORCE             0.142       AT NODE        365   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.358       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.526E-03   AT NODE        583   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.130E+04   TIME AVG. MOMENT      1.052E+04
 LARGEST RESIDUAL MOMENT            -4.54       AT NODE        847   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.057E-03   AT NODE        514   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.577E-05   AT NODE        846   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    20 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4499    
     TOTAL ARC LENGTH    1.52    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    21 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.171E+03   TIME AVG. FORCE       4.004E+03
 LARGEST RESIDUAL FORCE            -1.860E+04   AT NODE        809   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.248       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.248       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.240E+04   TIME AVG. MOMENT      1.109E+04
 LARGEST RESIDUAL MOMENT           -1.258E+05   AT NODE        356   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.277E-03   AT NODE        589   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.277E-03   AT NODE        589   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =  0.10000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.962E+03   TIME AVG. FORCE       3.995E+03
 LARGEST RESIDUAL FORCE              58.0       AT NODE        660   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.        -0.348       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.100       AT NODE        588   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.252E+04   TIME AVG. MOMENT      1.109E+04
 LARGEST RESIDUAL MOMENT           -1.286E+03   AT NODE        809   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      6.869E-03   AT NODE        623   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     4.653E-03   AT NODE        809   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6882
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         2.124e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

 ***ERROR: Process terminated by external request (SIGTERM or SIGINT received).



     ANALYSIS SUMMARY:
     TOTAL OF         21  INCREMENTS
                       0  CUTBACKS IN AUTOMATIC INCREMENTATION
                      55  ITERATIONS INCLUDING CONTACT ITERATIONS IF PRESENT
                      55  PASSES THROUGH THE EQUATION SOLVER OF WHICH 
                      55  INVOLVE MATRIX DECOMPOSITION, INCLUDING
                       0  DECOMPOSITION(S) OF THE MASS MATRIX
                       1  REORDERING OF EQUATIONS TO MINIMIZE WAVEFRONT
                       0  ADDITIONAL RESIDUAL EVALUATIONS FOR LINE SEARCHES
                       0  ADDITIONAL OPERATOR EVALUATIONS FOR LINE SEARCHES
                       2  WARNING MESSAGES DURING USER INPUT PROCESSING
                       1  WARNING MESSAGES DURING ANALYSIS
                       0  ANALYSIS WARNINGS ARE NUMERICAL PROBLEM MESSAGES
                       0  ANALYSIS WARNINGS ARE NEGATIVE EIGENVALUE MESSAGES
                       1  ERROR MESSAGES



     JOB TIME SUMMARY
       USER TIME (SEC)      =      37.    
       SYSTEM TIME (SEC)    =      3.6    
       TOTAL CPU TIME (SEC) =      40.    
       WALLCLOCK TIME (SEC) =           41
       MEMORY PEAK (GB)     =            0
