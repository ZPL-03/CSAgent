1

   Abaqus 2023                                  Date 09-Nov-2026   Time 14:30:49
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

     CHARACTERISTIC ELEMENT LENGTH      19.9    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

     COLLECTING MODEL CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

     COLLECTING STEP CONSTRAINT INFORMATION FOR OVERCONSTRAINT CHECKS

 ***WARNING: The 3-direction at one or more points in one or more layers in 780 
             elements as defined in *ORIENTATION are in the opposite direction 
             to the element normals. Either the 1 or 2 and the 3-direction 
             defined in *ORIENTATION will be reversed. The elements have been 
             identified in element set WarnElem3DirOppElemNormalStep1Inc1.


  INCREMENT     1 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       26.1       TIME AVG. FORCE        26.1    
 LARGEST RESIDUAL FORCE             0.138       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.504E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.504E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                      77.7       TIME AVG. MOMENT       77.7    
 LARGEST RESIDUAL MOMENT           -0.139       AT NODE        104   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.606E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.606E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.20000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.20000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       26.1       TIME AVG. FORCE        26.1    
 LARGEST RESIDUAL FORCE             1.104E-06   AT NODE       1548   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.506E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.460E-05   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      77.9       TIME AVG. MOMENT       77.9    
 LARGEST RESIDUAL MOMENT            1.168E-04   AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.607E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.346E-07   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     1 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         9.9961E-03
     TOTAL ARC LENGTH   1.000E-02, INCREMENT OF ARC LENGTH   1.000E-02


  INCREMENT     2 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       102.       TIME AVG. FORCE        64.1    
 LARGEST RESIDUAL FORCE             0.134       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.510E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.510E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    1.724E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                      156.       TIME AVG. MOMENT       117.    
 LARGEST RESIDUAL MOMENT            0.181       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.607E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.607E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       102.       TIME AVG. FORCE        64.1    
 LARGEST RESIDUAL FORCE             2.085E-06   AT NODE       1548   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         1.512E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.453E-05   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      156.       TIME AVG. MOMENT       117.    
 LARGEST RESIDUAL MOMENT            1.682E-04   AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.607E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.318E-07   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    1.500E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     2 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         1.9984E-02
     TOTAL ARC LENGTH   2.000E-02, INCREMENT OF ARC LENGTH   1.000E-02


  INCREMENT     3 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       177.       TIME AVG. FORCE        102.    
 LARGEST RESIDUAL FORCE             0.302       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         2.274E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.274E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    3.897E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                      274.       TIME AVG. MOMENT       169.    
 LARGEST RESIDUAL MOMENT            0.440       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.411E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.411E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       176.       TIME AVG. FORCE        102.    
 LARGEST RESIDUAL FORCE             8.214E-06   AT NODE       1548   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         2.280E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        7.924E-05   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      274.       TIME AVG. MOMENT       170.    
 LARGEST RESIDUAL MOMENT            6.272E-04   AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.411E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.886E-07   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    2.250E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     3 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         3.4951E-02
     TOTAL ARC LENGTH   3.500E-02, INCREMENT OF ARC LENGTH   1.500E-02


  INCREMENT     4 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       288.       TIME AVG. FORCE        148.    
 LARGEST RESIDUAL FORCE             0.680       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         3.432E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.432E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    8.828E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                      453.       TIME AVG. MOMENT       240.    
 LARGEST RESIDUAL MOMENT             1.04       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.617E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.617E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       288.       TIME AVG. FORCE        148.    
 LARGEST RESIDUAL FORCE             3.101E-05   AT NODE       1548   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         3.446E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.843E-04   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      454.       TIME AVG. MOMENT       241.    
 LARGEST RESIDUAL MOMENT            2.246E-03   AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.618E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.292E-06   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    3.375E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     4 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         5.7364E-02
     TOTAL ARC LENGTH   5.750E-02, INCREMENT OF ARC LENGTH   2.250E-02


  INCREMENT     5 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       452.       TIME AVG. FORCE        209.    
 LARGEST RESIDUAL FORCE              1.53       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         5.198E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        5.198E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                      725.       TIME AVG. MOMENT       337.    
 LARGEST RESIDUAL MOMENT             2.41       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -5.428E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.428E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       452.       TIME AVG. FORCE        209.    
 LARGEST RESIDUAL FORCE             1.146E-04   AT NODE       1548   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         5.231E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        4.366E-04   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                      727.       TIME AVG. MOMENT       338.    
 LARGEST RESIDUAL MOMENT            7.844E-03   AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -5.429E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.409E-06   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    5.063E-02

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     5 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         9.0889E-02
     TOTAL ARC LENGTH   9.125E-02, INCREMENT OF ARC LENGTH   3.375E-02


  INCREMENT     6 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.20000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.20000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                       696.       TIME AVG. FORCE        290.    
 LARGEST RESIDUAL FORCE              3.43       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         7.915E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        7.915E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.141E+03   TIME AVG. MOMENT       472.    
 LARGEST RESIDUAL MOMENT             5.53       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.146E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.146E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                       696.       TIME AVG. FORCE        290.    
 LARGEST RESIDUAL FORCE            -5.569E-04   AT NODE        792   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         7.994E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.064E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.726E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.147E+03   TIME AVG. MOMENT       473.    
 LARGEST RESIDUAL MOMENT            2.683E-02   AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.146E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.309E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                       696.       TIME AVG. FORCE        290.    
 LARGEST RESIDUAL FORCE            -2.136E-07   AT NODE       1511   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         7.994E-02   AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.373E-08   AT NODE        157   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.147E+03   TIME AVG. MOMENT       473.    
 LARGEST RESIDUAL MOMENT           -3.255E-06   AT NODE         84   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.146E-04   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     2.205E-09   AT NODE       1496   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    7.594E-02

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     6 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.1409    
     TOTAL ARC LENGTH   0.142    , INCREMENT OF ARC LENGTH   5.063E-02


  INCREMENT     7 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.054E+03   TIME AVG. FORCE        399.    
 LARGEST RESIDUAL FORCE              7.70       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.122       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.122       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.789E+03   TIME AVG. MOMENT       661.    
 LARGEST RESIDUAL MOMENT             12.5       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.222E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.222E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.052E+03   TIME AVG. FORCE        399.    
 LARGEST RESIDUAL FORCE            -3.752E-03   AT NODE        792   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.124       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.698E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.316E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.803E+03   TIME AVG. MOMENT       663.    
 LARGEST RESIDUAL MOMENT            8.946E-02   AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.221E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.287E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      1.052E+03   TIME AVG. FORCE        399.    
 LARGEST RESIDUAL FORCE             9.082E-07   AT NODE       1518   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.124       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.865E-07   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.803E+03   TIME AVG. MOMENT       663.    
 LARGEST RESIDUAL MOMENT            2.058E-05   AT NODE       1548   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.221E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.940E-09   AT NODE        118   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED
          ARC LENGTH INCREMENT MAY NOW INCREASE TO    0.100    

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     7 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.2153    
     TOTAL ARC LENGTH   0.218    , INCREMENT OF ARC LENGTH   7.594E-02


  INCREMENT     8 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.519E+03   TIME AVG. FORCE        539.    
 LARGEST RESIDUAL FORCE              13.2       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.166       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.166       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.694E+03   TIME AVG. MOMENT       917.    
 LARGEST RESIDUAL MOMENT             22.9       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.607E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.607E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.514E+03   TIME AVG. FORCE        538.    
 LARGEST RESIDUAL FORCE            -1.552E-02   AT NODE        792   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.170       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        5.520E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -6.487E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.722E+03   TIME AVG. MOMENT       920.    
 LARGEST RESIDUAL MOMENT            0.245       AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.604E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -6.602E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      1.514E+03   TIME AVG. FORCE        538.    
 LARGEST RESIDUAL FORCE            -5.402E-06   AT NODE         62   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.170       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -1.737E-06   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.722E+03   TIME AVG. MOMENT       920.    
 LARGEST RESIDUAL MOMENT            9.773E-05   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.604E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.874E-08   AT NODE       1479   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     8 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.3116    
     TOTAL ARC LENGTH   0.318    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT     9 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      1.972E+03   TIME AVG. FORCE        698.    
 LARGEST RESIDUAL FORCE              12.9       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.175       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.175       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     3.683E+03   TIME AVG. MOMENT      1.227E+03
 LARGEST RESIDUAL MOMENT             26.9       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.599E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.599E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      1.965E+03   TIME AVG. FORCE        697.    
 LARGEST RESIDUAL FORCE            -2.036E-02   AT NODE        792   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.179       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        6.588E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.043E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     3.715E+03   TIME AVG. MOMENT      1.231E+03
 LARGEST RESIDUAL MOMENT            0.440       AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.592E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -7.647E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      1.965E+03   TIME AVG. FORCE        697.    
 LARGEST RESIDUAL FORCE            -1.221E-05   AT NODE         62   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.179       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.178E-06   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     3.715E+03   TIME AVG. MOMENT      1.231E+03
 LARGEST RESIDUAL MOMENT            1.952E-04   AT NODE       1548   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.592E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -4.585E-08   AT NODE       1479   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT     9 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4053    
     TOTAL ARC LENGTH   0.418    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    10 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.404E+03   TIME AVG. FORCE        868.    
 LARGEST RESIDUAL FORCE              12.3       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.185       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.185       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     4.756E+03   TIME AVG. MOMENT      1.583E+03
 LARGEST RESIDUAL MOMENT             30.5       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.579E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.579E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.395E+03   TIME AVG. FORCE        867.    
 LARGEST RESIDUAL FORCE            -2.498E-02   AT NODE        792   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.189       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        7.670E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.557E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     4.791E+03   TIME AVG. MOMENT      1.587E+03
 LARGEST RESIDUAL MOMENT            0.706       AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.567E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.582E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      2.395E+03   TIME AVG. FORCE        867.    
 LARGEST RESIDUAL FORCE            -2.321E-05   AT NODE         62   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.189       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.125E-06   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     4.791E+03   TIME AVG. MOMENT      1.587E+03
 LARGEST RESIDUAL MOMENT           -3.442E-04   AT NODE         67   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.567E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -6.675E-08   AT NODE       1479   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    10 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.4951    
     TOTAL ARC LENGTH   0.518    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    11 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      2.808E+03   TIME AVG. FORCE       1.043E+03
 LARGEST RESIDUAL FORCE              11.5       AT NODE       1466   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.195       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.195       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     5.922E+03   TIME AVG. MOMENT      1.981E+03
 LARGEST RESIDUAL MOMENT             33.6       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.545E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.545E-03   AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      2.798E+03   TIME AVG. FORCE       1.042E+03
 LARGEST RESIDUAL FORCE            -2.764E-02   AT NODE        805   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.200       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.555E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -2.063E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     5.958E+03   TIME AVG. MOMENT      1.984E+03
 LARGEST RESIDUAL MOMENT             1.02       AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.604E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.156E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      2.798E+03   TIME AVG. FORCE       1.042E+03
 LARGEST RESIDUAL FORCE             3.606E-05   AT NODE       1518   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.200       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        6.463E-07   AT NODE        183   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     5.958E+03   TIME AVG. MOMENT      1.984E+03
 LARGEST RESIDUAL MOMENT            5.344E-04   AT NODE        521   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.604E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.767E-08   AT NODE       1479   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    11 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.5799    
     TOTAL ARC LENGTH   0.618    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    12 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            1

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.182E+03   TIME AVG. FORCE       1.221E+03
 LARGEST RESIDUAL FORCE              12.9       AT NODE        831   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.205       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.205       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     7.179E+03   TIME AVG. MOMENT      2.417E+03
 LARGEST RESIDUAL MOMENT             35.7       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.728E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.728E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.169E+03   TIME AVG. FORCE       1.219E+03
 LARGEST RESIDUAL FORCE            -2.621E-02   AT NODE        805   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.209       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.972E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.829E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     7.214E+03   TIME AVG. MOMENT      2.420E+03
 LARGEST RESIDUAL MOMENT             1.34       AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.819E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -9.104E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.169E+03   TIME AVG. FORCE       1.219E+03
 LARGEST RESIDUAL FORCE             4.166E-05   AT NODE       1518   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.209       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.951E-06   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     7.214E+03   TIME AVG. MOMENT      2.420E+03
 LARGEST RESIDUAL MOMENT            8.036E-04   AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.819E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.056E-07   AT NODE       1496   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    12 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.6582    
     TOTAL ARC LENGTH   0.718    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    13 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.518E+03   TIME AVG. FORCE       1.396E+03
 LARGEST RESIDUAL FORCE              15.7       AT NODE        831   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.214       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.214       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     8.522E+03   TIME AVG. MOMENT      2.889E+03
 LARGEST RESIDUAL MOMENT             36.9       AT NODE       1509   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.940E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.940E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.503E+03   TIME AVG. FORCE       1.395E+03
 LARGEST RESIDUAL FORCE             3.009E-02   AT NODE       1492   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.217       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        8.723E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    1.670E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     8.552E+03   TIME AVG. MOMENT      2.892E+03
 LARGEST RESIDUAL MOMENT             1.56       AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.023E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.318E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          ROTATION CORRECTION TOO LARGE COMPARED TO ROTATION INCREMENT
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.503E+03   TIME AVG. FORCE       1.395E+03
 LARGEST RESIDUAL FORCE             2.908E-05   AT NODE         87   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.217       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.123E-05   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     8.552E+03   TIME AVG. MOMENT      2.892E+03
 LARGEST RESIDUAL MOMENT            2.411E-03   AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.023E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.597E-07   AT NODE        820   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    13 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.7290    
     TOTAL ARC LENGTH   0.818    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    14 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.814E+03   TIME AVG. FORCE       1.568E+03
 LARGEST RESIDUAL FORCE             -29.2       AT NODE       1518   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.220       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.220       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     9.934E+03   TIME AVG. MOMENT      3.395E+03
 LARGEST RESIDUAL MOMENT            -212.       AT NODE       1518   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.131E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.131E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.800E+03   TIME AVG. FORCE       1.567E+03
 LARGEST RESIDUAL FORCE            -3.253E-02   AT NODE        123   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.222       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        7.877E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    8.780E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     9.959E+03   TIME AVG. MOMENT      3.396E+03
 LARGEST RESIDUAL MOMENT             1.92       AT NODE         62   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.201E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -6.981E-05   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    6.318E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    14 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.7916    
     TOTAL ARC LENGTH   0.918    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    15 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.071E+03   TIME AVG. FORCE       1.734E+03
 LARGEST RESIDUAL FORCE              378.       AT NODE         97   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.224       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.224       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.139E+04   TIME AVG. MOMENT      3.929E+03
 LARGEST RESIDUAL MOMENT            2.657E+03   AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.292E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.292E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.055E+03   TIME AVG. FORCE       1.733E+03
 LARGEST RESIDUAL FORCE            -8.420E-02   AT NODE       1537   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.225       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        7.108E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -1.584E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.142E+04   TIME AVG. MOMENT      3.931E+03
 LARGEST RESIDUAL MOMENT             7.19       AT NODE       1535   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.348E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.304E-04   AT NODE       1536   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    3.528E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    15 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.8458    
     TOTAL ARC LENGTH    1.02    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    16 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.290E+03   TIME AVG. FORCE       1.893E+03
 LARGEST RESIDUAL FORCE             -396.       AT NODE       1518   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.289E+04   TIME AVG. MOMENT      4.491E+03
 LARGEST RESIDUAL MOMENT            2.591E+03   AT NODE       1534   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.416E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.416E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.275E+03   TIME AVG. FORCE       1.892E+03
 LARGEST RESIDUAL FORCE            -8.113E-02   AT NODE         80   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        5.895E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    1.206E-06
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.291E+04   TIME AVG. MOMENT      4.492E+03
 LARGEST RESIDUAL MOMENT            -7.69       AT NODE       1518   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.457E-03   AT NODE        803   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.244E-04   AT NODE       1534   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -3.719E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    16 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.8923    
     TOTAL ARC LENGTH    1.12    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    17 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.473E+03   TIME AVG. FORCE       2.044E+03
 LARGEST RESIDUAL FORCE              281.       AT NODE         64   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.227       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.227       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.441E+04   TIME AVG. MOMENT      5.076E+03
 LARGEST RESIDUAL MOMENT            1.821E+03   AT NODE         64   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.508E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.508E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.460E+03   TIME AVG. FORCE       2.043E+03
 LARGEST RESIDUAL FORCE             6.339E-02   AT NODE         76   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.227       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        4.424E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    9.995E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.443E+04   TIME AVG. MOMENT      5.077E+03
 LARGEST RESIDUAL MOMENT             5.24       AT NODE         64   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.537E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     9.333E-05   AT NODE         64   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    2.716E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    17 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.9326    
     TOTAL ARC LENGTH    1.22    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    18 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.630E+03   TIME AVG. FORCE       2.187E+03
 LARGEST RESIDUAL FORCE              195.       AT NODE         65   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.227       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.227       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.595E+04   TIME AVG. MOMENT      5.681E+03
 LARGEST RESIDUAL MOMENT            1.312E+03   AT NODE         65   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.576E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.576E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.621E+03   TIME AVG. FORCE       2.186E+03
 LARGEST RESIDUAL FORCE             4.332E-02   AT NODE       1522   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.227       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        3.234E-03   AT NODE        781   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    7.195E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.596E+04   TIME AVG. MOMENT      5.681E+03
 LARGEST RESIDUAL MOMENT             3.50       AT NODE         65   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.596E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     6.264E-05   AT NODE         65   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.684E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    18 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.9674    
     TOTAL ARC LENGTH    1.32    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    19 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.766E+03   TIME AVG. FORCE       2.322E+03
 LARGEST RESIDUAL FORCE              176.       AT NODE        100   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.749E+04   TIME AVG. MOMENT      6.303E+03
 LARGEST RESIDUAL MOMENT            1.146E+03   AT NODE       1532   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.625E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.625E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.758E+03   TIME AVG. FORCE       2.321E+03
 LARGEST RESIDUAL FORCE            -3.762E-02   AT NODE         77   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.401E-03   AT NODE        817   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION   -5.122E-07
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     1.749E+04   TIME AVG. MOMENT      6.303E+03
 LARGEST RESIDUAL MOMENT             2.98       AT NODE       1532   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.639E-03   AT NODE        803   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     5.799E-05   AT NODE       1532   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.515E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    19 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.9976    
     TOTAL ARC LENGTH    1.42    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    20 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.884E+03   TIME AVG. FORCE       2.450E+03
 LARGEST RESIDUAL FORCE              163.       AT NODE         79   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.904E+04   TIME AVG. MOMENT      6.939E+03
 LARGEST RESIDUAL MOMENT            -770.       AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.661E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.661E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.878E+03   TIME AVG. FORCE       2.449E+03
 LARGEST RESIDUAL FORCE             3.283E-02   AT NODE         92   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.225       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        2.004E-03   AT NODE        297   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.904E+04   TIME AVG. MOMENT      6.940E+03
 LARGEST RESIDUAL MOMENT            -3.78       AT NODE         79   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.670E-03   AT NODE        803   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     3.532E-05   AT NODE       1558   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION    1.780E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    20 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR          1.024    
     TOTAL ARC LENGTH    1.52    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    21 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.988E+03   TIME AVG. FORCE       2.570E+03
 LARGEST RESIDUAL FORCE              81.7       AT NODE         61   DOF  2
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.225       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.225       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.059E+04   TIME AVG. MOMENT      7.589E+03
 LARGEST RESIDUAL MOMENT             552.       AT NODE       1549   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.687E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.687E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.983E+03   TIME AVG. FORCE       2.570E+03
 LARGEST RESIDUAL FORCE            -2.599E-02   AT NODE       1549   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.225       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        1.482E-03   AT NODE        261   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.059E+04   TIME AVG. MOMENT      7.589E+03
 LARGEST RESIDUAL MOMENT             1.90       AT NODE         63   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.693E-03   AT NODE        829   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.722E-05   AT NODE       1547   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -9.393E-08
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   2 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  2 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    21 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR          1.047    
     TOTAL ARC LENGTH    1.62    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    22 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.068E+03   TIME AVG. FORCE       2.683E+03
 LARGEST RESIDUAL FORCE            -7.811E+03   AT NODE        808   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.226       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.194E+04   TIME AVG. MOMENT      8.242E+03
 LARGEST RESIDUAL MOMENT           -5.792E+04   AT NODE        808   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.710E-03   AT NODE        803   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     2.710E-03   AT NODE        803   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      5.003E+03   TIME AVG. FORCE       2.680E+03
 LARGEST RESIDUAL FORCE             -13.5       AT NODE        791   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.277       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        6.019E-02   AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.186E+04   TIME AVG. MOMENT      8.238E+03
 LARGEST RESIDUAL MOMENT             301.       AT NODE        808   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.271E-03   AT NODE        792   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.171E-03   AT NODE        791   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      5.003E+03   TIME AVG. FORCE       2.680E+03
 LARGEST RESIDUAL FORCE            -4.218E-02   AT NODE        782   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.277       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.292E-04   AT NODE        791   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.186E+04   TIME AVG. MOMENT      8.238E+03
 LARGEST RESIDUAL MOMENT             2.58       AT NODE        894   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.266E-03   AT NODE        792   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.382E-05   AT NODE        895   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -2.903E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    22 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR          1.051    
     TOTAL ARC LENGTH    1.72    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    23 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      5.016E+03   TIME AVG. FORCE       2.782E+03
 LARGEST RESIDUAL FORCE            -2.883E+04   AT NODE        817   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.236       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.236       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.207E+04   TIME AVG. MOMENT      8.839E+03
 LARGEST RESIDUAL MOMENT            1.929E+05   AT NODE        817   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.771E-03   AT NODE        794   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.771E-03   AT NODE        794   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.511E+03   TIME AVG. FORCE       2.760E+03
 LARGEST RESIDUAL FORCE             -427.       AT NODE        818   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.473       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.299       AT NODE        816   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.101E+04   TIME AVG. MOMENT      8.793E+03
 LARGEST RESIDUAL MOMENT            1.929E+03   AT NODE        808   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.232E-02   AT NODE        791   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.080E-02   AT NODE        791   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      4.514E+03   TIME AVG. FORCE       2.760E+03
 LARGEST RESIDUAL FORCE              1.04       AT NODE        808   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.474       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -9.484E-03   AT NODE        815   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    2.315E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.103E+04   TIME AVG. MOMENT      8.794E+03
 LARGEST RESIDUAL MOMENT             21.4       AT NODE        807   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.224E-02   AT NODE        791   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.732E-04   AT NODE        633   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -1.918E-06
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    23 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.9460    
     TOTAL ARC LENGTH    1.82    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    24 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.519E+03   TIME AVG. FORCE       2.833E+03
 LARGEST RESIDUAL FORCE             2.829E+04   AT NODE        626   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.252       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.252       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.135E+04   TIME AVG. MOMENT      9.317E+03
 LARGEST RESIDUAL MOMENT           -1.635E+05   AT NODE        971   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.799E-03   AT NODE        794   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.799E-03   AT NODE        794   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      4.054E+03   TIME AVG. FORCE       2.814E+03
 LARGEST RESIDUAL FORCE              230.       AT NODE        789   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.451       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.199       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.011E+04   TIME AVG. MOMENT      9.265E+03
 LARGEST RESIDUAL MOMENT            1.758E+03   AT NODE        902   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.074E-02   AT NODE        973   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     9.299E-03   AT NODE        973   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      4.057E+03   TIME AVG. FORCE       2.814E+03
 LARGEST RESIDUAL FORCE            -0.701       AT NODE        886   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.449       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -5.259E-03   AT NODE        782   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF DISP.    CORRECTION    1.601E-05
 FORCE     EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 AVERAGE MOMENT                     2.012E+04   TIME AVG. MOMENT      9.266E+03
 LARGEST RESIDUAL MOMENT             11.3       AT NODE        851   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      1.067E-02   AT NODE        973   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.644E-04   AT NODE        581   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -1.053E-06
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    24 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.8455    
     TOTAL ARC LENGTH    1.92    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    25 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      4.074E+03   TIME AVG. FORCE       2.865E+03
 LARGEST RESIDUAL FORCE            -2.475E+04   AT NODE        808   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.270       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.270       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.066E+04   TIME AVG. MOMENT      9.722E+03
 LARGEST RESIDUAL MOMENT           -1.002E+05   AT NODE       1023   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -2.841E-03   AT NODE        794   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -2.841E-03   AT NODE        794   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.782E+03   TIME AVG. FORCE       2.853E+03
 LARGEST RESIDUAL FORCE              341.       AT NODE        808   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.560       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.290       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.981E+04   TIME AVG. MOMENT      9.688E+03
 LARGEST RESIDUAL MOMENT            1.810E+03   AT NODE        808   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -1.004E-02   AT NODE        860   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -8.269E-03   AT NODE        860   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.784E+03   TIME AVG. FORCE       2.853E+03
 LARGEST RESIDUAL FORCE              1.77       AT NODE        808   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.556       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -4.927E-03   AT NODE        808   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.982E+04   TIME AVG. MOMENT      9.688E+03
 LARGEST RESIDUAL MOMENT            -19.3       AT NODE        808   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.912E-03   AT NODE        860   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     1.316E-04   AT NODE        808   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -1.402E-06
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    25 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.7834    
     TOTAL ARC LENGTH    2.02    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    26 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.807E+03   TIME AVG. FORCE       2.890E+03
 LARGEST RESIDUAL FORCE             1.759E+04   AT NODE        791   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.281       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.281       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.042E+04   TIME AVG. MOMENT      1.010E+04
 LARGEST RESIDUAL MOMENT            8.818E+04   AT NODE       1007   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      2.929E-03   AT NODE        804   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     2.929E-03   AT NODE        804   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.581E+03   TIME AVG. FORCE       2.881E+03
 LARGEST RESIDUAL FORCE              148.       AT NODE        789   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.484       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.214       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     1.974E+04   TIME AVG. MOMENT      1.007E+04
 LARGEST RESIDUAL MOMENT           -1.267E+03   AT NODE        824   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -9.053E-03   AT NODE        791   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -6.736E-03   AT NODE        946   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.583E+03   TIME AVG. FORCE       2.881E+03
 LARGEST RESIDUAL FORCE            -0.644       AT NODE        824   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.480       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -3.878E-03   AT NODE        791   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     1.975E+04   TIME AVG. MOMENT      1.008E+04
 LARGEST RESIDUAL MOMENT            -9.76       AT NODE        825   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -8.969E-03   AT NODE        791   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -1.013E-04   AT NODE       1068   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 ESTIMATE OF ROTATION CORRECTION   -7.795E-07
 MOMENT    EQUILIB. ACCEPTED BASED ON SMALL RESIDUAL AND ESTIMATED CORRECTION

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    26 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.7379    
     TOTAL ARC LENGTH    2.12    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    27 STARTS. ATTEMPT NUMBER  1
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     1


 AVERAGE FORCE                      3.613E+03   TIME AVG. FORCE       2.908E+03
 LARGEST RESIDUAL FORCE            -1.572E+04   AT NODE        652   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.288       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.288       AT NODE        807   DOF  1
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.057E+04   TIME AVG. MOMENT      1.046E+04
 LARGEST RESIDUAL MOMENT           -4.306E+04   AT NODE       1033   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION     -3.043E-03   AT NODE        793   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -3.043E-03   AT NODE        793   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     2


 AVERAGE FORCE                      3.477E+03   TIME AVG. FORCE       2.903E+03
 LARGEST RESIDUAL FORCE              67.3       AT NODE        824   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.429       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.        0.149       AT NODE        738   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          FORCE     EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.

 AVERAGE MOMENT                     2.013E+04   TIME AVG. MOMENT      1.045E+04
 LARGEST RESIDUAL MOMENT            -834.       AT NODE        824   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      8.062E-03   AT NODE        634   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION     6.489E-03   AT NODE        634   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
          MOMENT    EQUILIBRIUM NOT ACHIEVED WITHIN TOLERANCE.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     9672
 	NUMBER OF RHS:           2
 	NUMBER OF FLOPS:         3.946e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =  0.10000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =  0.10000    
       ELAPSED WALLCLOCK TIME (SEC) =            0

               CONVERGENCE CHECKS FOR EQUILIBRIUM ITERATION     3


 AVERAGE FORCE                      3.478E+03   TIME AVG. FORCE       2.903E+03
 LARGEST RESIDUAL FORCE             0.329       AT NODE        808   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF DISP.         0.426       AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO DISP.       -2.669E-03   AT NODE        790   DOF  3
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE FORCE     EQUILIBRIUM EQUATIONS HAVE CONVERGED

 AVERAGE MOMENT                     2.013E+04   TIME AVG. MOMENT      1.045E+04
 LARGEST RESIDUAL MOMENT             5.46       AT NODE        824   DOF  5
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST INCREMENT OF ROTATION      8.008E-03   AT NODE        634   DOF  4
   INSTANCE: COMPOSITEHULL-1                                                                 
 LARGEST CORRECTION TO ROTATION    -5.929E-05   AT NODE        529   DOF  6
   INSTANCE: COMPOSITEHULL-1                                                                 
          THE MOMENT    EQUILIBRIUM EQUATIONS HAVE CONVERGED

 ITERATION SUMMARY FOR THE INCREMENT:   3 TOTAL ITERATIONS, OF WHICH
   0 ARE SEVERE DISCONTINUITY ITERATIONS AND  3 ARE EQUILIBRIUM ITERATIONS.


                                INCREMENT    27 SUMMARY


     CURRENT LOAD PROPORTIONALITY FACTOR         0.7139    
     TOTAL ARC LENGTH    2.22    , INCREMENT OF ARC LENGTH   0.100    


  INCREMENT    28 STARTS. ATTEMPT NUMBER  1

 ***ERROR: Process terminated by external request (SIGTERM or SIGINT received).



     ANALYSIS SUMMARY:
     TOTAL OF         28  INCREMENTS
                       0  CUTBACKS IN AUTOMATIC INCREMENTATION
                      69  ITERATIONS INCLUDING CONTACT ITERATIONS IF PRESENT
                      68  PASSES THROUGH THE EQUATION SOLVER OF WHICH 
                      69  INVOLVE MATRIX DECOMPOSITION, INCLUDING
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
       USER TIME (SEC)      =     1.07E+02
       SYSTEM TIME (SEC)    =      4.7    
       TOTAL CPU TIME (SEC) =     1.12E+02
       WALLCLOCK TIME (SEC) =          114
       MEMORY PEAK (GB)     =            0
