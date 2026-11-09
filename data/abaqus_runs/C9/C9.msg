1

   Abaqus 2023                                  Date 09-Nov-2026   Time 20:48:12
   For use by Supplied by Team-SolidSQUAD under license from Dassault Systemes or its subsidiary.

 CSDM_cph pressure hull linear buckling                                          
                                                                                 
 STEP    1     INCREMENT     1     STEP TIME    0.00    


                        S T E P       1     C A L C U L A T I O N   O F   E I G E N V A L U E S

                                            F O R   B U C K L I N G   P R E D I C T I O N



                                                                                          

     THE SUBSPACE ITERATION METHOD IS USED FOR THIS ANALYSIS
     NUMBER OF EIGENVALUES                      8
     MAXIMUM NUMBER OF ITERATIONS                    300
     NUMBER OF VECTORS IN ITERATION                   12
     THE BUCKLING MODE CONSTRAINTS 
      ARE DEFINED AS LOAD CASE 2
                              ONLY INITIAL STRESS EFFECTS ARE INCLUDED IN THE
                              STIFFNESS MATRIX

     THIS IS A LINEAR PERTURBATION STEP.
     ALL LOADS ARE DEFINED AS CHANGE IN LOAD TO THE REFERENCE STATE

     EXTRAPOLATION WILL NOT BE USED

     CHARACTERISTIC ELEMENT LENGTH      14.9    

     DETAILS REGARDING ACTUAL SOLUTION WAVEFRONT REQUESTED

     DETAILED OUTPUT OF DIAGNOSTICS TO DATABASE REQUESTED

     PRINT OF INCREMENT NUMBER, TIME, ETC., TO THE MESSAGE FILE EVERY     1  INCREMENTS

 ***WARNING: The 3-direction at one or more points in one or more layers in 480 
             elements as defined in *ORIENTATION are in the opposite direction 
             to the element normals. Either the 1 or 2 and the 3-direction 
             defined in *ORIENTATION will be reversed. The elements have been 
             identified in element set WarnElem3DirOppElemNormalStep1Inc1.

 ***WARNING: The local-3 direction (after additional rotation and permutation) 
             of the material orientation , specified via *ORIENTATION, is in 
             the plane of the SHELL, MEMBRANE, GASKET, COHESIVE, or SURFACE 
             element. The local-1 direction will be projected onto the element 
             surface and the positive element normal will be used as the 
             local-3 direction. The elements have been identified in element 
             set WarnElemUserNormMatOrient.
 
	SYMMETRIC DIRECT SPARSE SOLVER RUNNING ON
 	1 HOST:        1 MPI RANK  x 1 THREAD
 	NUMBER OF EQUATIONS:     6324
 	NUMBER OF RHS:           1
 	NUMBER OF FLOPS:         1.941e+08

     CHECK POINT  START OF SOLVER     

     CHECK POINT  END OF SOLVER       

       ELAPSED USER TIME (SEC)      =   0.0000    
       ELAPSED SYSTEM TIME (SEC)    =   0.0000    
       ELAPSED TOTAL CPU TIME (SEC) =   0.0000    
       ELAPSED WALLCLOCK TIME (SEC) =            0
 
     ITERATION 1
      1       8.570032e+02     
      2       8.641316e+02     
      3       8.805150e+02     
      4       8.941823e+02     
      5       9.092650e+02     
      6       9.214114e+02     
      7       9.316579e+02     
      8       9.540219e+02     
      9       9.906468e+02     
      10      1.009962e+03     
      11      1.041926e+03     
      12      3.568117e+03     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 2
      1       6.244373e+02     
      2       6.617696e+02     
      3       6.716364e+02     
      4       6.806607e+02     
      5       6.850473e+02     
      6       6.911443e+02     
      7       6.957739e+02     
      8       6.994707e+02     
      9       7.044077e+02     
      10      7.052821e+02     
      11      7.139947e+02     
      12      7.216188e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 3
      1       4.198120e+02     
      2       5.461339e+02     
      3       5.975750e+02     
      4       6.368400e+02     
      5       6.491743e+02     
      6       6.599786e+02     
      7       6.642586e+02     
      8       6.666833e+02     
      9       6.741828e+02     
      10      6.776483e+02     
      11      6.827316e+02     
      12      6.892273e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 4
      1       2.793968e+02     
      2       3.517164e+02     
      3       5.024427e+02     
      4       5.656684e+02     
      5       6.094548e+02     
      6       6.272355e+02     
      7       6.367210e+02     
      8       6.413935e+02     
      9       6.543947e+02     
      10      6.591053e+02     
      11      6.626735e+02     
      12      6.680716e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 5
      1       2.486260e+02     
      2       2.640336e+02     
      3       4.219995e+02     
      4       4.741515e+02     
      5       5.536071e+02     
      6       5.868104e+02     
      7       6.007011e+02     
      8       6.152981e+02     
      9       6.329065e+02     
      10      6.380756e+02     
      11      6.461395e+02     
      12      6.514448e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 6
      1       2.438883e+02     
      2       2.466050e+02     
      3       3.806613e+02     
      4       4.059305e+02     
      5       4.926125e+02     
      6       5.349116e+02     
      7       5.615376e+02     
      8       5.873305e+02     
      9       6.071293e+02     
      10      6.127683e+02     
      11      6.298264e+02     
      12      6.351229e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 7
      1       2.431552e+02     
      2       2.436416e+02     
      3       3.644208e+02     
      4       3.738945e+02     
      5       4.464174e+02     
      6       4.831469e+02     
      7       5.242774e+02     
      8       5.601687e+02     
      9       5.791812e+02     
      10      5.847292e+02     
      11      6.110896e+02     
      12      6.170826e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 8
      1       2.430337e+02     
      2       2.431234e+02     
      3       3.583480e+02     
      4       3.617629e+02     
      5       4.206736e+02     
      6       4.443663e+02     
      7       4.958311e+02     
      8       5.365963e+02     
      9       5.514654e+02     
      10      5.574577e+02     
      11      5.895930e+02     
      12      5.971881e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 9
      1       2.430121e+02     
      2       2.430293e+02     
      3       3.559816e+02     
      4       3.573071e+02     
      5       4.086595e+02     
      6       4.216107e+02     
      7       4.777150e+02     
      8       5.176098e+02     
      9       5.264700e+02     
      10      5.346174e+02     
      11      5.666617e+02     
      12      5.766858e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 10
      1       2.430081e+02     
      2       2.430115e+02     
      3       3.550372e+02     
      4       3.555917e+02     
      5       4.034375e+02     
      6       4.101108e+02     
      7       4.672710e+02     
      8       5.020020e+02     
      9       5.075913e+02     
      10      5.171944e+02     
      11      5.444833e+02     
      12      5.575739e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 11
      1       2.430073e+02     
      2       2.430080e+02     
      3       3.546570e+02     
      4       3.549014e+02     
      5       4.011831e+02     
      6       4.046347e+02     
      7       4.614729e+02     
      8       4.884308e+02     
      9       4.959650e+02     
      10      5.045833e+02     
      11      5.250497e+02     
      12      5.414620e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 0
 
     ITERATION 12
      1       2.430071e+02     
      2       2.430073e+02     
      3       3.545000e+02     
      4       3.546148e+02     
      5       4.001794e+02     
      6       4.020317e+02     
      7       4.582542e+02     
      8       4.783167e+02     
      9       4.883639e+02     
      10      4.956797e+02     
      11      5.093562e+02     
      12      5.289073e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 1
 
     ITERATION 13
      1       2.430071e+02     
      2       2.430072e+02     
      3       3.544327e+02     
      4       3.544912e+02     
      5       3.997071e+02     
      6       4.007564e+02     
      7       4.564313e+02     
      8       4.713519e+02     
      9       4.829323e+02     
      10      4.894071e+02     
      11      4.973860e+02     
      12      5.196001e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 2
 
     ITERATION 14
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.544028e+02     
      4       3.544351e+02     
      5       3.994688e+02     
      6       4.001014e+02     
      7       4.553696e+02     
      8       4.666018e+02     
      9       4.786777e+02     
      10      4.848714e+02     
      11      4.887090e+02     
      12      5.128677e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 2
 
     ITERATION 15
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543892e+02     
      4       3.544082e+02     
      5       3.993395e+02     
      6       3.997455e+02     
      7       4.547328e+02     
      8       4.633099e+02     
      9       4.747928e+02     
      10      4.811212e+02     
      11      4.832446e+02     
      12      5.080293e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 2
 
     ITERATION 16
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543830e+02     
      4       3.543945e+02     
      5       3.992647e+02     
      6       3.995404e+02     
      7       4.543394e+02     
      8       4.609668e+02     
      9       4.708377e+02     
      10      4.778272e+02     
      11      4.804437e+02     
      12      5.045317e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 2
 
     ITERATION 17
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543802e+02     
      4       3.543872e+02     
      5       3.992195e+02     
      6       3.994154e+02     
      7       4.540889e+02     
      8       4.592511e+02     
      9       4.670485e+02     
      10      4.754681e+02     
      11      4.787114e+02     
      12      5.019659e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 2
 
     ITERATION 18
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543788e+02     
      4       3.543832e+02     
      5       3.991913e+02     
      6       3.993353e+02     
      7       4.539241e+02     
      8       4.579633e+02     
      9       4.637201e+02     
      10      4.737393e+02     
      11      4.774828e+02     
      12      5.000429e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 2
 
     ITERATION 19
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543782e+02     
      4       3.543809e+02     
      5       3.991736e+02     
      6       3.992817e+02     
      7       4.538121e+02     
      8       4.569768e+02     
      9       4.609263e+02     
      10      4.723761e+02     
      11      4.765679e+02     
      12      4.985638e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 2
 
     ITERATION 20
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543779e+02     
      4       3.543796e+02     
      5       3.991623e+02     
      6       3.992447e+02     
      7       4.537333e+02     
      8       4.562060e+02     
      9       4.586411e+02     
      10      4.712418e+02     
      11      4.758664e+02     
      12      4.973930e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 3
 
     ITERATION 21
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543778e+02     
      4       3.543788e+02     
      5       3.991552e+02     
      6       3.992185e+02     
      7       4.536759e+02     
      8       4.555792e+02     
      9       4.568211e+02     
      10      4.702603e+02     
      11      4.753164e+02     
      12      4.964388e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 3
 
     ITERATION 22
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543784e+02     
      5       3.991507e+02     
      6       3.991995e+02     
      7       4.536316e+02     
      8       4.549371e+02     
      9       4.555212e+02     
      10      4.693847e+02     
      11      4.748778e+02     
      12      4.956382e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 3
 
     ITERATION 23
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543781e+02     
      5       3.991479e+02     
      6       3.991855e+02     
      7       4.535847e+02     
      8       4.540132e+02     
      9       4.549262e+02     
      10      4.685837e+02     
      11      4.745233e+02     
      12      4.949482e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 4
 
     ITERATION 24
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543779e+02     
      5       3.991462e+02     
      6       3.991752e+02     
      7       4.530981e+02     
      8       4.536012e+02     
      9       4.545969e+02     
      10      4.678354e+02     
      11      4.742338e+02     
      12      4.943380e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 4
 
     ITERATION 25
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543778e+02     
      5       3.991451e+02     
      6       3.991674e+02     
      7       4.524109e+02     
      8       4.535719e+02     
      9       4.543552e+02     
      10      4.671237e+02     
      11      4.739956e+02     
      12      4.937861e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 4
 
     ITERATION 26
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543778e+02     
      5       3.991444e+02     
      6       3.991616e+02     
      7       4.518695e+02     
      8       4.535548e+02     
      9       4.541683e+02     
      10      4.664368e+02     
      11      4.737983e+02     
      12      4.932765e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 4
 
     ITERATION 27
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991440e+02     
      6       3.991572e+02     
      7       4.514504e+02     
      8       4.535420e+02     
      9       4.540217e+02     
      10      4.657662e+02     
      11      4.736343e+02     
      12      4.927972e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 4
 
     ITERATION 28
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991438e+02     
      6       3.991538e+02     
      7       4.511283e+02     
      8       4.535318e+02     
      9       4.539059e+02     
      10      4.651055e+02     
      11      4.734974e+02     
      12      4.923394e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 5
 
     ITERATION 29
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991436e+02     
      6       3.991513e+02     
      7       4.508817e+02     
      8       4.535234e+02     
      9       4.538143e+02     
      10      4.644504e+02     
      11      4.733828e+02     
      12      4.918960e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 5
 
     ITERATION 30
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991435e+02     
      6       3.991493e+02     
      7       4.506933e+02     
      8       4.535162e+02     
      9       4.537416e+02     
      10      4.637980e+02     
      11      4.732867e+02     
      12      4.914617e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 5
 
     ITERATION 31
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991435e+02     
      6       3.991479e+02     
      7       4.505499e+02     
      8       4.535096e+02     
      9       4.536840e+02     
      10      4.631467e+02     
      11      4.732059e+02     
      12      4.910323e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 5
 
     ITERATION 32
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991435e+02     
      6       3.991468e+02     
      7       4.504407e+02     
      8       4.535032e+02     
      9       4.536385e+02     
      10      4.624963e+02     
      11      4.731380e+02     
      12      4.906047e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 5
 
     ITERATION 33
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991459e+02     
      7       4.503578e+02     
      8       4.534964e+02     
      9       4.536031e+02     
      10      4.618470e+02     
      11      4.730808e+02     
      12      4.901763e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 5
 
     ITERATION 34
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991453e+02     
      7       4.502949e+02     
      8       4.534886e+02     
      9       4.535763e+02     
      10      4.612002e+02     
      11      4.730325e+02     
      12      4.897455e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 5
 
     ITERATION 35
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991448e+02     
      7       4.502471e+02     
      8       4.534793e+02     
      9       4.535566e+02     
      10      4.605578e+02     
      11      4.729918e+02     
      12      4.893108e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 5
 
     ITERATION 36
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991444e+02     
      7       4.502109e+02     
      8       4.534685e+02     
      9       4.535430e+02     
      10      4.599220e+02     
      11      4.729574e+02     
      12      4.888717e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 37
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991442e+02     
      7       4.501835e+02     
      8       4.534566e+02     
      9       4.535338e+02     
      10      4.592956e+02     
      11      4.729283e+02     
      12      4.884276e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 38
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991440e+02     
      7       4.501627e+02     
      8       4.534439e+02     
      9       4.535275e+02     
      10      4.586815e+02     
      11      4.729037e+02     
      12      4.879785e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 39
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991438e+02     
      7       4.501470e+02     
      8       4.534307e+02     
      9       4.535232e+02     
      10      4.580829e+02     
      11      4.728828e+02     
      12      4.875246e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 40
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991437e+02     
      7       4.501351e+02     
      8       4.534167e+02     
      9       4.535201e+02     
      10      4.575029e+02     
      11      4.728651e+02     
      12      4.870664e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 41
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991436e+02     
      7       4.501260e+02     
      8       4.534014e+02     
      9       4.535178e+02     
      10      4.569446e+02     
      11      4.728501e+02     
      12      4.866046e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 42
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991436e+02     
      7       4.501192e+02     
      8       4.533838e+02     
      9       4.535160e+02     
      10      4.564114e+02     
      11      4.728373e+02     
      12      4.861400e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 43
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991435e+02     
      7       4.501140e+02     
      8       4.533624e+02     
      9       4.535146e+02     
      10      4.559068e+02     
      11      4.728265e+02     
      12      4.856735e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 44
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991435e+02     
      7       4.501101e+02     
      8       4.533346e+02     
      9       4.535136e+02     
      10      4.554349e+02     
      11      4.728172e+02     
      12      4.852061e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 45
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991435e+02     
      7       4.501071e+02     
      8       4.532963e+02     
      9       4.535127e+02     
      10      4.550012e+02     
      11      4.728094e+02     
      12      4.847390e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 46
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.501049e+02     
      8       4.532399e+02     
      9       4.535120e+02     
      10      4.546141e+02     
      11      4.728026e+02     
      12      4.842733e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 47
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.501031e+02     
      8       4.531533e+02     
      9       4.535114e+02     
      10      4.542861e+02     
      11      4.727969e+02     
      12      4.838101e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 48
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.501019e+02     
      8       4.530213e+02     
      9       4.535110e+02     
      10      4.540326e+02     
      11      4.727920e+02     
      12      4.833506e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 49
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.501009e+02     
      8       4.528383e+02     
      9       4.535106e+02     
      10      4.538587e+02     
      11      4.727877e+02     
      12      4.828960e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 50
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.501001e+02     
      8       4.526187e+02     
      9       4.535103e+02     
      10      4.537498e+02     
      11      4.727841e+02     
      12      4.824472e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 51
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500996e+02     
      8       4.523849e+02     
      9       4.535100e+02     
      10      4.536825e+02     
      11      4.727810e+02     
      12      4.820053e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 6
 
     ITERATION 52
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500991e+02     
      8       4.521533e+02     
      9       4.535098e+02     
      10      4.536393e+02     
      11      4.727783e+02     
      12      4.815715e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 53
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500988e+02     
      8       4.519328e+02     
      9       4.535096e+02     
      10      4.536101e+02     
      11      4.727760e+02     
      12      4.811464e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 54
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500985e+02     
      8       4.517275e+02     
      9       4.535095e+02     
      10      4.535895e+02     
      11      4.727740e+02     
      12      4.807312e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 55
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500984e+02     
      8       4.515392e+02     
      9       4.535093e+02     
      10      4.535742e+02     
      11      4.727723e+02     
      12      4.803263e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 56
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500982e+02     
      8       4.513680e+02     
      9       4.535092e+02     
      10      4.535626e+02     
      11      4.727708e+02     
      12      4.799327e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 57
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500981e+02     
      8       4.512136e+02     
      9       4.535091e+02     
      10      4.535535e+02     
      11      4.727695e+02     
      12      4.795508e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 58
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500980e+02     
      8       4.510751e+02     
      9       4.535091e+02     
      10      4.535463e+02     
      11      4.727684e+02     
      12      4.791812e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 59
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500980e+02     
      8       4.509515e+02     
      9       4.535090e+02     
      10      4.535404e+02     
      11      4.727674e+02     
      12      4.788244e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 60
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500979e+02     
      8       4.508416e+02     
      9       4.535090e+02     
      10      4.535356e+02     
      11      4.727665e+02     
      12      4.784805e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 61
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500979e+02     
      8       4.507443e+02     
      9       4.535089e+02     
      10      4.535316e+02     
      11      4.727658e+02     
      12      4.781499e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 62
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.506585e+02     
      9       4.535089e+02     
      10      4.535283e+02     
      11      4.727651e+02     
      12      4.778327e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 63
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.505831e+02     
      9       4.535088e+02     
      10      4.535255e+02     
      11      4.727645e+02     
      12      4.775290e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 64
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.505170e+02     
      9       4.535088e+02     
      10      4.535231e+02     
      11      4.727640e+02     
      12      4.772388e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 65
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.504592e+02     
      9       4.535088e+02     
      10      4.535211e+02     
      11      4.727635e+02     
      12      4.769620e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 66
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.504088e+02     
      9       4.535088e+02     
      10      4.535193e+02     
      11      4.727631e+02     
      12      4.766985e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 67
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.503649e+02     
      9       4.535087e+02     
      10      4.535178e+02     
      11      4.727628e+02     
      12      4.764482e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 68
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.503269e+02     
      9       4.535087e+02     
      10      4.535166e+02     
      11      4.727625e+02     
      12      4.762106e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 69
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.502940e+02     
      9       4.535087e+02     
      10      4.535155e+02     
      11      4.727622e+02     
      12      4.759857e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 70
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500978e+02     
      8       4.502656e+02     
      9       4.535087e+02     
      10      4.535145e+02     
      11      4.727619e+02     
      12      4.757729e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 71
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.502410e+02     
      9       4.535087e+02     
      10      4.535137e+02     
      11      4.727617e+02     
      12      4.755721e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 72
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.502200e+02     
      9       4.535087e+02     
      10      4.535130e+02     
      11      4.727615e+02     
      12      4.753827e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 73
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.502018e+02     
      9       4.535087e+02     
      10      4.535124e+02     
      11      4.727613e+02     
      12      4.752044e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 74
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501863e+02     
      9       4.535087e+02     
      10      4.535119e+02     
      11      4.727612e+02     
      12      4.750367e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 75
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501730e+02     
      9       4.535087e+02     
      10      4.535114e+02     
      11      4.727610e+02     
      12      4.748792e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 76
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501616e+02     
      9       4.535087e+02     
      10      4.535110e+02     
      11      4.727609e+02     
      12      4.747314e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 77
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501519e+02     
      9       4.535087e+02     
      10      4.535107e+02     
      11      4.727608e+02     
      12      4.745930e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 78
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501437e+02     
      9       4.535087e+02     
      10      4.535104e+02     
      11      4.727607e+02     
      12      4.744634e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 79
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501366e+02     
      9       4.535087e+02     
      10      4.535102e+02     
      11      4.727606e+02     
      12      4.743421e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 80
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501306e+02     
      9       4.535087e+02     
      10      4.535100e+02     
      11      4.727605e+02     
      12      4.742289e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 81
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501255e+02     
      9       4.535087e+02     
      10      4.535098e+02     
      11      4.727604e+02     
      12      4.741231e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 82
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501212e+02     
      9       4.535087e+02     
      10      4.535096e+02     
      11      4.727604e+02     
      12      4.740245e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 83
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501176e+02     
      9       4.535087e+02     
      10      4.535095e+02     
      11      4.727603e+02     
      12      4.739325e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 84
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501145e+02     
      9       4.535087e+02     
      10      4.535094e+02     
      11      4.727602e+02     
      12      4.738469e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 85
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501118e+02     
      9       4.535087e+02     
      10      4.535093e+02     
      11      4.727602e+02     
      12      4.737672e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 86
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501096e+02     
      9       4.535087e+02     
      10      4.535092e+02     
      11      4.727601e+02     
      12      4.736930e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 87
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501078e+02     
      9       4.535087e+02     
      10      4.535091e+02     
      11      4.727601e+02     
      12      4.736241e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 88
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501062e+02     
      9       4.535087e+02     
      10      4.535090e+02     
      11      4.727600e+02     
      12      4.735600e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 89
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501048e+02     
      9       4.535087e+02     
      10      4.535090e+02     
      11      4.727600e+02     
      12      4.735005e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 90
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501037e+02     
      9       4.535087e+02     
      10      4.535089e+02     
      11      4.727600e+02     
      12      4.734453e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 91
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501028e+02     
      9       4.535087e+02     
      10      4.535089e+02     
      11      4.727599e+02     
      12      4.733940e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 92
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501020e+02     
      9       4.535087e+02     
      10      4.535089e+02     
      11      4.727599e+02     
      12      4.733465e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 93
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501013e+02     
      9       4.535087e+02     
      10      4.535088e+02     
      11      4.727599e+02     
      12      4.733024e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 94
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501007e+02     
      9       4.535087e+02     
      10      4.535088e+02     
      11      4.727599e+02     
      12      4.732615e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 95
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.501003e+02     
      9       4.535087e+02     
      10      4.535088e+02     
      11      4.727598e+02     
      12      4.732237e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 7
 
     ITERATION 96
      1       2.430071e+02     
      2       2.430071e+02     
      3       3.543777e+02     
      4       3.543777e+02     
      5       3.991434e+02     
      6       3.991434e+02     
      7       4.500977e+02     
      8       4.500999e+02     
      9       4.535087e+02     
      10      4.535088e+02     
      11      4.727598e+02     
      12      4.731886e+02     
 
     NUMBER OF EIGENVALUES CONVERGED UPTO THIS ITERATION = 8


          THE ANALYSIS HAS BEEN COMPLETED



     ANALYSIS SUMMARY:
     TOTAL OF          1  INCREMENTS
                       0  CUTBACKS IN AUTOMATIC INCREMENTATION
                       1  ITERATIONS INCLUDING CONTACT ITERATIONS IF PRESENT
                       1  PASSES THROUGH THE EQUATION SOLVER OF WHICH 
                       1  INVOLVE MATRIX DECOMPOSITION, INCLUDING
                       0  DECOMPOSITION(S) OF THE MASS MATRIX
                       1  REORDERING OF EQUATIONS TO MINIMIZE WAVEFRONT
                       0  ADDITIONAL RESIDUAL EVALUATIONS FOR LINE SEARCHES
                       0  ADDITIONAL OPERATOR EVALUATIONS FOR LINE SEARCHES
                       2  WARNING MESSAGES DURING USER INPUT PROCESSING
                       2  WARNING MESSAGES DURING ANALYSIS
                       0  ANALYSIS WARNINGS ARE NUMERICAL PROBLEM MESSAGES
                       0  ANALYSIS WARNINGS ARE NEGATIVE EIGENVALUE MESSAGES
                       0  ERROR MESSAGES



     JOB TIME SUMMARY
       USER TIME (SEC)      =      2.4    
       SYSTEM TIME (SEC)    =     0.40    
       TOTAL CPU TIME (SEC) =      2.8    
       WALLCLOCK TIME (SEC) =            3
       MEMORY PEAK (GB)     =            0
