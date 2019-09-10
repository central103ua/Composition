#!/bin/bash
DST_DIR=ekstrenka/InitData
#CALL_PRIORITY=CallPriority
#CALL_STATIONS=CallStations
#CALL_RESULT=CallResult
#MIS_TYPE=MisType
#FACILITY_TYPE=FacilityType
#LOCATION_TYPE=LocationType
#ADDRESS_TYPE=AddressType
#STAFFTITLE=StaffTitle
#STAFFQUALIFICATION=StaffQualification
#sPERMISSION=Permission
# CHIEFCOMPLAIN=ChiefComplain
# BREATHSTATE=BreathState
# CONSCSTATE=ConscState
# SITUATION=Situation
# PATIENTSTATE=PatientState

# CREW_STATUS=CrewStatus
# CAR_TYPE=CarType
# CAR_STATUS=CarStatus
# CAR_OWNER=CarOwner

set -x
python manage.py loaddata ekstrenka/InitData/CallPriority.xml
python manage.py loaddata ekstrenka/InitData/CallStations.xml
python manage.py loaddata ekstrenka/InitData/CallResult.xml

python manage.py loaddata ekstrenka/InitData/StaffTitle.xml
python manage.py loaddata ekstrenka/InitData/StaffQualification.xml

#python manage.py loaddata ekstrenka/InitData/$MIS_TYPE.xml
python manage.py loaddata ekstrenka/InitData/FacilityType.xml
python manage.py loaddata ekstrenka/InitData/LocationType.xml
python manage.py loaddata ekstrenka/InitData/AddressType.xml

python manage.py loaddata ekstrenka/InitData/CarType.xml
python manage.py loaddata ekstrenka/InitData/CarStatus.xml
python manage.py loaddata ekstrenka/InitData/CarOwner.xml

python manage.py loaddata ekstrenka/InitData/CrewStatus.xml

python manage.py loaddata ekstrenka/InitData/Permission.xml

python manage.py loaddata ekstrenka/InitData/ChiefComplain.xml
python manage.py loaddata ekstrenka/InitData/BreathState.xml
python manage.py loaddata ekstrenka/InitData/ConscState.xml
python manage.py loaddata ekstrenka/InitData/Situation.xml
python manage.py loaddata ekstrenka/InitData/PatientState.xml
python manage.py loaddata ekstrenka/InitData/State.xml
python manage.py loaddata ekstrenka/InitData/District.xml

python manage.py loaddata ekstrenka/InitData/PushStatus.xml
python manage.py loaddata ekstrenka/InitData/FilterLogic.xml

python manage.py loaddata ekstrenka/InitData/IntercallSatus.xml

python manage.py loaddata ekstrenka/InitData/MKXcode1.xml
python manage.py loaddata ekstrenka/InitData/MKXcode2.xml
python manage.py loaddata ekstrenka/InitData/MKXcode3.xml
#python manage.py loaddata ekstrenka/InitData/MKX.xml
python manage.py loaddata ekstrenka/InitData/MKXfull.xml

python manage.py loaddata ekstrenka/InitData/NoResult.xml
python manage.py loaddata ekstrenka/InitData/AddrDocType.xml
python manage.py loaddata ekstrenka/InitData/TheResult.xml
python manage.py loaddata ekstrenka/InitData/ResultAction.xml

set +x
