"""
Copyright (C) 2016 Interactive Brokers LLC. All rights reserved.  This code is
subject to the terms and conditions of the IB API Non-Commercial License or the
 IB API Commercial License, as applicable. 
"""

from ibapi.object_implem import Object


class FaAllocationSamples(Object):
    FaOneGroup = "".join(("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        , "<ListOfGroups>"                                                   
                    , "<Group>"                                              
                            , "<name>Equal_Quantity</name>"                  
                            , "<ListOfAccts varName=\"list\">"               
                                    #Replace with your own accountIds
                                    , "<String>DU119915</String>"            
                                    , "<String>DU119916</String>"            
                            , "</ListOfAccts>"                               
                            , "<defaultMethod>EqualQuantity</defaultMethod>" 
                    , "</Group>"                                             
            , "</ListOfGroups>"))

    FaTwoGroups = "".join(("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"               
                ,"<ListOfGroups>"                                            
                    , "<Group>"                                              
                            , "<name>Equal_Quantity</name>"                  
                            , "<ListOfAccts varName=\"list\">"               
                                    #Replace with your own accountIds                            
                                    , "<String>DU119915</String>"                                
                                    , "<String>DU119916</String>"            
                            , "</ListOfAccts>"                               
                            , "<defaultMethod>EqualQuantity</defaultMethod>" 
                    , "</Group>"                                             
                    , "<Group>"                                              
                            , "<name>Pct_Change</name>"                      
                            , "<ListOfAccts varName=\"list\">"               
                #Replace with your own accountIds                            
                , "<String>DU119915</String>"                                
                                    , "<String>DU119916</String>"            
                            , "</ListOfAccts>"                               
                            , "<defaultMethod>PctChange</defaultMethod>"     
                    , "</Group>"                                             
            , "</ListOfGroups>"))

    FaOneProfile = "".join(("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"              
                , "<ListOfAllocationProfiles>"                               
                    , "<AllocationProfile>"                                  
                            , "<name>Percent_60_40</name>"                   
                            , "<type>1</type>"                               
                            , "<ListOfAllocations varName=\"listOfAllocations\">"
                                    , "<Allocation>"                         
                                            #Replace with your own accountIds                        
                                            , "<acct>DU119915</acct>"                                
                                            , "<amount>60.0</amount>"        
                                    , "</Allocation>"                        
                                    , "<Allocation>"                         
                                            #Replace with your own accountIds                        
                                            , "<acct>DU119916</acct>"                                
                                            , "<amount>40.0</amount>"        
                                    , "</Allocation>"                        
                            , "</ListOfAllocations>"                         
                    , "</AllocationProfile>"                                 
            , "</ListOfAllocationProfiles>"))

    FaTwoProfiles = "".join(("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"             
                , "<ListOfAllocationProfiles>"                               
                    , "<AllocationProfile>"                                  
                            , "<name>Percent_60_40</name>"                   
                            , "<type>1</type>"                               
                            , "<ListOfAllocations varName=\"listOfAllocations\">" 
                                    , "<Allocation>"                         
                                            #Replace with your own accountIds                        
                                            , "<acct>DU119915</acct>"                                
                                            , "<amount>60.0</amount>"        
                                    , "</Allocation>"                        
                                    , "<Allocation>"                         
                                            #Replace with your own accountIds                        
                                            , "<acct>DU119916</acct>"                                
                                            , "<amount>40.0</amount>"        
                                    , "</Allocation>"                        
                            , "</ListOfAllocations>"                         
                    , "</AllocationProfile>"                                 
                    , "<AllocationProfile>"                                  
                            , "<name>Ratios_2_1</name>"                      
                            , "<type>1</type>"                               
                            , "<ListOfAllocations varName=\"listOfAllocations\">"
                                    , "<Allocation>"                         
                                            #Replace with your own accountIds                        
                                            , "<acct>DU119915</acct>"                                
                                            , "<amount>2.0</amount>"         
                                    , "</Allocation>"                        
                                    , "<Allocation>"                         
                                            #Replace with your own accountIds                        
                                            , "<acct>DU119916</acct>"                                
                                            , "<amount>1.0</amount>"         
                                    , "</Allocation>"                        
                            , "</ListOfAllocations>"                         
                    , "</AllocationProfile>"                                 
            , "</ListOfAllocationProfiles>"))




