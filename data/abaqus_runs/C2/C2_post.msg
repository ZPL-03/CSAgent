1

   Abaqus 2023                                  Date 09-Nov-2026   Time 14:35:32
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

     CHARACTERISTIC ELEMENT LENGTH      20.0    

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


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       33.9       TIME AVG. FORCE        33.9    
 LARGEST RESIDUAL FORCE             0.230       AT NODE       1359   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         2.458E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.458E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                      151.       TIME AVG. MOMENT       151.    
 LARGEST RESIDUAL MOMENT            0.259       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.130E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     2.130E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       33.8       TIME AVG. FORCE        33.8    
 LARGEST RESIDUAL FORCE            -5.412E-06   AT NODE       1390   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         2.464E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.444E-05   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      151.       TIME AVG. MOMENT       151.    
 LARGEST RESIDUAL MOMENT            3.616E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.128E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.034E-06   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     1 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         9.9850E-03
     TOTAL ARC LENGTH   1.000E-02, INCREMENT OF ARC LENGTH   1.000E-02


  INCREMENT     2 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       127.       TIME AVG. FORCE        80.2    
 LARGEST RESIDUAL FORCE             0.224       AT NODE       1359   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         2.470E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.470E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    3.493E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                      304.       TIME AVG. MOMENT       227.    
 LARGEST RESIDUAL MOMENT            0.343       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.127E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     2.127E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       126.       TIME AVG. FORCE        80.2    
 LARGEST RESIDUAL FORCE            -7.422E-06   AT NODE       1390   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         2.476E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.346E-05   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      304.       TIME AVG. MOMENT       228.    
 LARGEST RESIDUAL MOMENT            5.268E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.126E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.015E-06   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    1.500E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     2 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         1.9937E-02
     TOTAL ARC LENGTH   2.000E-02, INCREMENT OF ARC LENGTH   1.000E-02


  INCREMENT     3 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       220.       TIME AVG. FORCE        127.    
 LARGEST RESIDUAL FORCE             0.501       AT NODE       1359   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         3.724E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.724E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    7.894E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                      534.       TIME AVG. MOMENT       330.    
 LARGEST RESIDUAL MOMENT            0.835       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      3.186E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     3.186E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       219.       TIME AVG. FORCE        127.    
 LARGEST RESIDUAL FORCE             2.750E-05   AT NODE         91   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         3.736E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.899E-04   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      535.       TIME AVG. MOMENT       330.    
 LARGEST RESIDUAL MOMENT           -2.017E-03   AT NODE       1375   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      3.183E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.298E-06   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    2.250E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     3 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         3.4802E-02
     TOTAL ARC LENGTH   3.500E-02, INCREMENT OF ARC LENGTH   1.500E-02


  INCREMENT     4 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       358.       TIME AVG. FORCE        184.    
 LARGEST RESIDUAL FORCE              1.12       AT NODE       1359   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         5.628E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        5.628E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                      885.       TIME AVG. MOMENT       469.    
 LARGEST RESIDUAL MOMENT             1.97       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      4.769E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     4.769E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       358.       TIME AVG. FORCE        184.    
 LARGEST RESIDUAL FORCE            -1.003E-04   AT NODE       1405   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         5.655E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        4.357E-04   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      887.       TIME AVG. MOMENT       470.    
 LARGEST RESIDUAL MOMENT           -7.571E-03   AT NODE       1375   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      4.762E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.245E-06   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                       358.       TIME AVG. FORCE        184.    
 LARGEST RESIDUAL FORCE            -1.137E-07   AT NODE       1322   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         5.655E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        6.652E-08   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      887.       TIME AVG. MOMENT       470.    
 LARGEST RESIDUAL MOMENT            1.935E-06   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      4.762E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.075E-09   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    3.375E-02

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     4 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         5.6949E-02
     TOTAL ARC LENGTH   5.750E-02, INCREMENT OF ARC LENGTH   2.250E-02


  INCREMENT     5 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       564.       TIME AVG. FORCE        260.    
 LARGEST RESIDUAL FORCE              2.50       AT NODE       1359   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         8.538E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.538E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.422E+03   TIME AVG. MOMENT       660.    
 LARGEST RESIDUAL MOMENT             4.52       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      7.129E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     7.129E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       562.       TIME AVG. FORCE        260.    
 LARGEST RESIDUAL FORCE            -3.603E-04   AT NODE       1405   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         8.599E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.011E-03   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.458E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.428E+03   TIME AVG. MOMENT       661.    
 LARGEST RESIDUAL MOMENT           -2.844E-02   AT NODE       1375   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      7.110E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.208E-05   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                       562.       TIME AVG. FORCE        260.    
 LARGEST RESIDUAL FORCE            -2.062E-07   AT NODE       1369   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         8.599E-02   AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.159E-07   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.428E+03   TIME AVG. MOMENT       661.    
 LARGEST RESIDUAL MOMENT            1.007E-05   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      7.110E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.643E-09   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    5.063E-02

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     5 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         8.9809E-02
     TOTAL ARC LENGTH   9.125E-02, INCREMENT OF ARC LENGTH   3.375E-02


  INCREMENT     6 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       865.       TIME AVG. FORCE        361.    
 LARGEST RESIDUAL FORCE              5.53       AT NODE       1359   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.130       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.130       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.253E+03   TIME AVG. MOMENT       926.    
 LARGEST RESIDUAL MOMENT             10.2       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.063E-03   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.063E-03   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       862.       TIME AVG. FORCE        360.    
 LARGEST RESIDUAL FORCE            -2.303E-03   AT NODE        750   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.132       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.376E-03   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -9.900E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.266E+03   TIME AVG. MOMENT       929.    
 LARGEST RESIDUAL MOMENT           -0.108       AT NODE       1375   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.058E-03   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.805E-05   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                       862.       TIME AVG. FORCE        360.    
 LARGEST RESIDUAL FORCE            -6.413E-07   AT NODE        695   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.132       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        6.158E-07   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.266E+03   TIME AVG. MOMENT       929.    
 LARGEST RESIDUAL MOMENT            4.654E-05   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.058E-03   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.155E-08   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    7.594E-02

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     6 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.1382    
     TOTAL ARC LENGTH   0.142    , INCREMENT OF ARC LENGTH   5.063E-02


  INCREMENT     7 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.301E+03   TIME AVG. FORCE        495.    
 LARGEST RESIDUAL FORCE              12.5       AT NODE        742   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.200       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.200       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.557E+03   TIME AVG. MOMENT      1.304E+03
 LARGEST RESIDUAL MOMENT             22.6       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.637E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.637E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.293E+03   TIME AVG. FORCE        494.    
 LARGEST RESIDUAL FORCE             1.406E-02   AT NODE        715   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.203       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        5.652E-03   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    6.339E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     3.589E+03   TIME AVG. MOMENT      1.309E+03
 LARGEST RESIDUAL MOMENT           -0.420       AT NODE       1375   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.703E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -6.549E-05   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      1.293E+03   TIME AVG. FORCE        494.    
 LARGEST RESIDUAL FORCE             4.038E-06   AT NODE       1406   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.203       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.115E-06   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.589E+03   TIME AVG. MOMENT      1.309E+03
 LARGEST RESIDUAL MOMENT            1.470E-04   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.703E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     3.135E-08   AT NODE        728   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    0.100    

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     7 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.2085    
     TOTAL ARC LENGTH   0.218    , INCREMENT OF ARC LENGTH   7.594E-02


  INCREMENT     8 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.850E+03   TIME AVG. FORCE        663.    
 LARGEST RESIDUAL FORCE              25.4       AT NODE        742   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.273       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.273       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     5.395E+03   TIME AVG. MOMENT      1.820E+03
 LARGEST RESIDUAL MOMENT             39.6       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.362E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.362E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.835E+03   TIME AVG. FORCE        661.    
 LARGEST RESIDUAL FORCE             4.595E-02   AT NODE        707   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.278       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.028E-02   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    1.861E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     5.449E+03   TIME AVG. MOMENT      1.826E+03
 LARGEST RESIDUAL MOMENT            -1.17       AT NODE       1375   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.478E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.154E-04   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =  0.10000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.20000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      1.835E+03   TIME AVG. FORCE        661.    
 LARGEST RESIDUAL FORCE             2.029E-05   AT NODE       1375   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.278       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.361E-06   AT NODE        364   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     5.450E+03   TIME AVG. MOMENT      1.826E+03
 LARGEST RESIDUAL MOMENT           -5.779E-04   AT NODE        505   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.478E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.002E-08   AT NODE       1339   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     8 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.2962    
     TOTAL ARC LENGTH   0.318    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT     9 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.346E+03   TIME AVG. FORCE        848.    
 LARGEST RESIDUAL FORCE              30.4       AT NODE        742   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.285       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.285       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     7.389E+03   TIME AVG. MOMENT      2.444E+03
 LARGEST RESIDUAL MOMENT             44.0       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.630E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.630E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.329E+03   TIME AVG. FORCE        847.    
 LARGEST RESIDUAL FORCE             3.844E-02   AT NODE        715   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.289       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.024E-02   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    1.296E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     7.439E+03   TIME AVG. MOMENT      2.450E+03
 LARGEST RESIDUAL MOMENT            -1.56       AT NODE       1375   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.740E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.095E-04   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      2.329E+03   TIME AVG. FORCE        847.    
 LARGEST RESIDUAL FORCE            -3.406E-05   AT NODE        742   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.289       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.419E-06   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     7.439E+03   TIME AVG. MOMENT      2.450E+03
 LARGEST RESIDUAL MOMENT            1.608E-03   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.740E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.654E-07   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     9 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.3773    
     TOTAL ARC LENGTH   0.418    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    10 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.800E+03   TIME AVG. FORCE       1.042E+03
 LARGEST RESIDUAL FORCE              35.4       AT NODE        742   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.294       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.294       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     9.502E+03   TIME AVG. MOMENT      3.155E+03
 LARGEST RESIDUAL MOMENT             46.9       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.885E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.885E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.782E+03   TIME AVG. FORCE       1.040E+03
 LARGEST RESIDUAL FORCE            -3.507E-02   AT NODE         98   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.298       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        9.620E-03   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -9.525E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     9.545E+03   TIME AVG. MOMENT      3.159E+03
 LARGEST RESIDUAL MOMENT             1.99       AT NODE        727   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.983E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.745E-05   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      2.782E+03   TIME AVG. FORCE       1.040E+03
 LARGEST RESIDUAL FORCE            -6.983E-05   AT NODE        742   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.298       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.706E-05   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     9.545E+03   TIME AVG. MOMENT      3.160E+03
 LARGEST RESIDUAL MOMENT            3.871E-03   AT NODE        712   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.983E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.637E-07   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    10 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4511    
     TOTAL ARC LENGTH   0.518    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    11 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.205E+03   TIME AVG. FORCE       1.237E+03
 LARGEST RESIDUAL FORCE              40.1       AT NODE        742   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.302       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.302       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.171E+04   TIME AVG. MOMENT      3.937E+03
 LARGEST RESIDUAL MOMENT             48.3       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.113E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.113E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.186E+03   TIME AVG. FORCE       1.235E+03
 LARGEST RESIDUAL FORCE            -3.635E-02   AT NODE         98   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.305       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.525E-03   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -7.726E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.175E+04   TIME AVG. MOMENT      3.940E+03
 LARGEST RESIDUAL MOMENT            -2.41       AT NODE        738   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.194E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.147E-05   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.186E+03   TIME AVG. FORCE       1.235E+03
 LARGEST RESIDUAL FORCE            -1.134E-04   AT NODE        742   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.305       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.469E-05   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.175E+04   TIME AVG. MOMENT      3.940E+03
 LARGEST RESIDUAL MOMENT           -7.685E-03   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.195E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.364E-07   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    11 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.5173    
     TOTAL ARC LENGTH   0.618    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    12 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.562E+03   TIME AVG. FORCE       1.429E+03
 LARGEST RESIDUAL FORCE              44.6       AT NODE        707   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.307       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.307       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.400E+04   TIME AVG. MOMENT      4.778E+03
 LARGEST RESIDUAL MOMENT             48.6       AT NODE         82   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.305E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.305E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.545E+03   TIME AVG. FORCE       1.428E+03
 LARGEST RESIDUAL FORCE            -3.424E-02   AT NODE         98   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.309       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        7.180E-03   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -5.517E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.402E+04   TIME AVG. MOMENT      4.780E+03
 LARGEST RESIDUAL MOMENT            -2.71       AT NODE        738   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.370E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -6.457E-05   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.545E+03   TIME AVG. FORCE       1.428E+03
 LARGEST RESIDUAL FORCE             1.591E-04   AT NODE        739   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.309       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.931E-05   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.402E+04   TIME AVG. MOMENT      4.780E+03
 LARGEST RESIDUAL MOMENT            1.191E-02   AT NODE        744   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.370E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     3.662E-07   AT NODE        728   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    12 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.5760    
     TOTAL ARC LENGTH   0.718    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    13 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.875E+03   TIME AVG. FORCE       1.616E+03
 LARGEST RESIDUAL FORCE             -357.       AT NODE       1406   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.311       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.311       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.634E+04   TIME AVG. MOMENT      5.669E+03
 LARGEST RESIDUAL MOMENT           -2.214E+03   AT NODE       1406   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.460E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.460E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.859E+03   TIME AVG. FORCE       1.615E+03
 LARGEST RESIDUAL FORCE             7.135E-02   AT NODE       1376   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.311       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        5.946E-03   AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.187E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.636E+04   TIME AVG. MOMENT      5.671E+03
 LARGEST RESIDUAL MOMENT             5.98       AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.508E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.136E-04   AT NODE       1406   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    3.068E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    13 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.6276    
     TOTAL ARC LENGTH   0.818    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    14 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.148E+03   TIME AVG. FORCE       1.796E+03
 LARGEST RESIDUAL FORCE              470.       AT NODE         90   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.313       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.313       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.871E+04   TIME AVG. MOMENT      6.602E+03
 LARGEST RESIDUAL MOMENT            2.684E+03   AT NODE         59   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.580E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.580E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.135E+03   TIME AVG. FORCE       1.795E+03
 LARGEST RESIDUAL FORCE            -0.115       AT NODE         90   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.313       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        4.913E-03   AT NODE        364   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.199E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.873E+04   TIME AVG. MOMENT      6.604E+03
 LARGEST RESIDUAL MOMENT            -8.76       AT NODE       1375   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.615E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.483E-04   AT NODE         89   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -4.886E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    14 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.6728    
     TOTAL ARC LENGTH   0.918    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    15 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.387E+03   TIME AVG. FORCE       1.968E+03
 LARGEST RESIDUAL FORCE             -302.       AT NODE       1408   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.313       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.313       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.112E+04   TIME AVG. MOMENT      7.571E+03
 LARGEST RESIDUAL MOMENT           -1.957E+03   AT NODE       1408   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.672E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.672E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.375E+03   TIME AVG. FORCE       1.967E+03
 LARGEST RESIDUAL FORCE             7.198E-02   AT NODE       1409   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.314       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.742E-03   AT NODE       1163   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -8.925E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.113E+04   TIME AVG. MOMENT      7.572E+03
 LARGEST RESIDUAL MOMENT             5.91       AT NODE         60   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.697E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.002E-04   AT NODE       1389   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -3.043E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    15 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.7126    
     TOTAL ARC LENGTH    1.02    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    16 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.592E+03   TIME AVG. FORCE       2.131E+03
 LARGEST RESIDUAL FORCE            -5.702E+03   AT NODE        741   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.314       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.314       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.348E+04   TIME AVG. MOMENT      8.567E+03
 LARGEST RESIDUAL MOMENT            4.245E+04   AT NODE        725   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.744E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.744E-03   AT NODE        752   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.568E+03   TIME AVG. FORCE       2.129E+03
 LARGEST RESIDUAL FORCE             -3.50       AT NODE        726   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.313       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.929E-02   AT NODE        771   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.184E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.347E+04   TIME AVG. MOMENT      8.566E+03
 LARGEST RESIDUAL MOMENT            -250.       AT NODE        725   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.802E-03   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.382E-03   AT NODE        708   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      4.568E+03   TIME AVG. FORCE       2.129E+03
 LARGEST RESIDUAL FORCE             3.768E-02   AT NODE        725   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.313       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        9.456E-05   AT NODE        724   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.347E+04   TIME AVG. MOMENT      8.566E+03
 LARGEST RESIDUAL MOMENT            -1.53       AT NODE        646   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.802E-03   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.796E-05   AT NODE        647   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    16 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.7445    
     TOTAL ARC LENGTH    1.12    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    17 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.666E+03   TIME AVG. FORCE       2.279E+03
 LARGEST RESIDUAL FORCE             2.396E+04   AT NODE        786   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.327       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.327       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.421E+04   TIME AVG. MOMENT      9.486E+03
 LARGEST RESIDUAL MOMENT            1.817E+05   AT NODE        663   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      3.897E-03   AT NODE        744   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     3.897E-03   AT NODE        744   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.203E+03   TIME AVG. FORCE       2.251E+03
 LARGEST RESIDUAL FORCE             -302.       AT NODE        710   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.494       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.255       AT NODE        740   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.345E+04   TIME AVG. MOMENT      9.442E+03
 LARGEST RESIDUAL MOMENT           -1.519E+03   AT NODE        710   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.201E-02   AT NODE        757   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     9.659E-03   AT NODE        757   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      4.206E+03   TIME AVG. FORCE       2.251E+03
 LARGEST RESIDUAL FORCE             0.396       AT NODE        708   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.493       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -5.775E-03   AT NODE        710   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    7.554E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.347E+04   TIME AVG. MOMENT      9.443E+03
 LARGEST RESIDUAL MOMENT             11.5       AT NODE        725   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.190E-02   AT NODE        757   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.343E-04   AT NODE        896   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.019E-06
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    17 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.6837    
     TOTAL ARC LENGTH    1.22    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    18 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.268E+03   TIME AVG. FORCE       2.363E+03
 LARGEST RESIDUAL FORCE            -2.489E+04   AT NODE        694   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.343       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.343       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.395E+04   TIME AVG. MOMENT      1.025E+04
 LARGEST RESIDUAL MOMENT           -1.322E+05   AT NODE        734   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.044E-03   AT NODE        768   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.044E-03   AT NODE        768   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.808E+03   TIME AVG. FORCE       2.338E+03
 LARGEST RESIDUAL FORCE              195.       AT NODE        725   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.503       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -0.231       AT NODE        724   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.291E+04   TIME AVG. MOMENT      1.019E+04
 LARGEST RESIDUAL MOMENT           -1.419E+03   AT NODE        694   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.231E-02   AT NODE        770   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.004E-03   AT NODE        770   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.811E+03   TIME AVG. FORCE       2.338E+03
 LARGEST RESIDUAL FORCE             0.502       AT NODE        725   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.500       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        6.712E-03   AT NODE        724   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    1.724E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.292E+04   TIME AVG. MOMENT      1.019E+04
 LARGEST RESIDUAL MOMENT             14.0       AT NODE        725   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.221E-02   AT NODE        770   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.569E-04   AT NODE        904   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -1.543E-06
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    18 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.6158    
     TOTAL ARC LENGTH    1.32    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    19 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.862E+03   TIME AVG. FORCE       2.418E+03
 LARGEST RESIDUAL FORCE            -2.247E+04   AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.362       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.362       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.353E+04   TIME AVG. MOMENT      1.089E+04
 LARGEST RESIDUAL MOMENT            1.294E+05   AT NODE        490   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.125E-03   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.125E-03   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.520E+03   TIME AVG. FORCE       2.400E+03
 LARGEST RESIDUAL FORCE              151.       AT NODE        716   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.551       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.189       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.248E+04   TIME AVG. MOMENT      1.084E+04
 LARGEST RESIDUAL MOMENT           -1.558E+03   AT NODE        716   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.059E-02   AT NODE        716   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.655E-03   AT NODE        733   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.522E+03   TIME AVG. FORCE       2.400E+03
 LARGEST RESIDUAL FORCE            -0.741       AT NODE        717   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.549       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.135E-03   AT NODE        749   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.250E+04   TIME AVG. MOMENT      1.084E+04
 LARGEST RESIDUAL MOMENT            -13.0       AT NODE        717   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.050E-02   AT NODE        716   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.165E-04   AT NODE        481   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -9.722E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    19 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.5660    
     TOTAL ARC LENGTH    1.42    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    20 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.566E+03   TIME AVG. FORCE       2.459E+03
 LARGEST RESIDUAL FORCE            -2.111E+04   AT NODE        874   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.378       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.378       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.344E+04   TIME AVG. MOMENT      1.147E+04
 LARGEST RESIDUAL MOMENT            8.015E+04   AT NODE        490   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -4.199E-03   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.199E-03   AT NODE        721   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.311E+03   TIME AVG. FORCE       2.446E+03
 LARGEST RESIDUAL FORCE              114.       AT NODE        747   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.557       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.179       AT NODE        670   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.239E+04   TIME AVG. MOMENT      1.142E+04
 LARGEST RESIDUAL MOMENT            1.912E+03   AT NODE        592   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.904E-03   AT NODE        765   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     6.756E-03   AT NODE        747   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.312E+03   TIME AVG. FORCE       2.446E+03
 LARGEST RESIDUAL FORCE             0.863       AT NODE        592   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.555       AT NODE        717   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.611E-03   AT NODE        716   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.240E+04   TIME AVG. MOMENT      1.142E+04
 LARGEST RESIDUAL MOMENT             14.3       AT NODE        591   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.840E-03   AT NODE        765   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     9.910E-05   AT NODE        530   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    7.422E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    20 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.5300    
     TOTAL ARC LENGTH    1.52    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    21 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     8742
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.049e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
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
       USER TIME (SEC)      =     1.03E+02
       SYSTEM TIME (SEC)    =      3.2    
       TOTAL CPU TIME (SEC) =     1.06E+02
       WALLCLOCK TIME (SEC) =          109
       MEMORY PEAK (GB)     =            0
