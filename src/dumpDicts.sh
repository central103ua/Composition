#!/bin/bash
DST_DIR=ekstrenka/InitData
CALL_PRIORITY=CallPriority
CALL_STATIONS=CallStations
CALL_RESULT=CallResult
MIS_TYPE=MisType
FACILITY_TYPE=FacilityType
LOCATION_TYPE=LocationType
ADDRESS_TYPE=AddressType
PATIENTS=Patient
ADDRESSES=Address
COMPLAIN=Complain
STAFFTITLE=StaffTitle
STAFFQUALIFICATION=StaffQualification
PERMISSION=Permission
CHIEFCOMPLAIN=ChiefComplain
BREATHSTATE=BreathState
CONSCSTATE=ConscState
SITUATION=Situation
PATIENTSTATE=PatientState

CREW_STATUS=CrewStatus
CAR_TYPE=CarType
CAR_STATUS=CarStatus
CAR_OWNER=CarOwner

set -x
python manage.py dumpdata callcard.$CALL_PRIORITY --indent=2 --format=xml > $DST_DIR/$CALL_PRIORITY.xml
python manage.py dumpdata callcard.$CALL_STATIONS --indent=2 --format=xml > $DST_DIR/$CALL_STATIONS.xml
python manage.py dumpdata callcard.$CALL_RESULT --indent=2 --format=xml > $DST_DIR/$CALL_RESULT.xml

python manage.py dumpdata mis.$STAFFTITLE --indent=2 --format=xml > $DST_DIR/$STAFFTITLE.xml
python manage.py dumpdata mis.$STAFFQUALIFICATION --indent=2 --format=xml > $DST_DIR/$STAFFQUALIFICATION.xml

python manage.py dumpdata mis.Mis --indent=2 --format=xml > ekstrenka/InitData/Mis.xml
python manage.py dumpdata mis.$MIS_TYPE --indent=2 --format=xml > $DST_DIR/$MIS_TYPE.xml
python manage.py dumpdata mis.$FACILITY_TYPE --indent=2 --format=xml > $DST_DIR/$FACILITY_TYPE.xml
python manage.py dumpdata mis.$LOCATION_TYPE --indent=2 --format=xml > $DST_DIR/$LOCATION_TYPE.xml
python manage.py dumpdata mis.$ADDRESS_TYPE --indent=2 --format=xml > $DST_DIR/$ADDRESS_TYPE.xml

python manage.py dumpdata mis.$CAR_TYPE --indent=2 --format=xml > $DST_DIR/$CAR_TYPE.xml
python manage.py dumpdata mis.$CAR_STATUS --indent=2 --format=xml > $DST_DIR/$CAR_STATUS.xml
python manage.py dumpdata mis.$CAR_OWNER --indent=2 --format=xml > $DST_DIR/$CAR_OWNER.xml

python manage.py dumpdata crew.$CREW_STATUS --indent=2 --format=xml > $DST_DIR/$CREW_STATUS.xml

python manage.py dumpdata accounts.Permission --indent=2 --format=xml > $DST_DIR/Permission.xml

python manage.py dumpdata patients.ChiefComplain --indent=2 --format=xml > $DST_DIR/ChiefComplain.xml
python manage.py dumpdata patients.BreathState --indent=2 --format=xml > $DST_DIR/BreathState.xml
python manage.py dumpdata patients.ConscState --indent=2 --format=xml > $DST_DIR/ConscState.xml
python manage.py dumpdata patients.Situation --indent=2 --format=xml > $DST_DIR/Situation.xml
python manage.py dumpdata patients.PatientState --indent=2 --format=xml > $DST_DIR/PatientState.xml
python manage.py dumpdata patients.State --indent=2 --format=xml > ekstrenka/InitData/State.xml
python manage.py dumpdata patients.District --indent=2 --format=xml > ekstrenka/InitData/District.xml

python manage.py dumpdata pushapi.PushStatus --indent=2 --format=xml > $DST_DIR/PushStatus.xml
python manage.py dumpdata pushapi.FilterLogic --indent=2 --format=xml > $DST_DIR/FilterLogic.xml

python manage.py dumpdata heartbeat.IntercallSatus --indent=2 --format=xml > ekstrenka/InitData/IntercallSatus.xml

python manage.py dumpdata medrecord.MKXcode1 --indent=2 --format=xml > ekstrenka/InitData/MKXcode1.xml
python manage.py dumpdata medrecord.MKXcode2 --indent=2 --format=xml > ekstrenka/InitData/MKXcode2.xml
python manage.py dumpdata medrecord.MKXcode3 --indent=2 --format=xml > ekstrenka/InitData/MKXcode3.xml
#python manage.py dumpdata medrecord.MKX --indent=2 --format=xml > ekstrenka/InitData/MKX.xml
python manage.py dumpdata medrecord.MKXfull --indent=2 --format=xml > ekstrenka/InitData/MKXfull.xml

python manage.py dumpdata medrecord.NoResult --indent=2 --format=xml > ekstrenka/InitData/NoResult.xml
python manage.py dumpdata medrecord.AddrDocType --indent=2 --format=xml > ekstrenka/InitData/AddrDocType.xml
python manage.py dumpdata medrecord.TheResult --indent=2 --format=xml > ekstrenka/InitData/TheResult.xml
python manage.py dumpdata medrecord.ResultAction --indent=2 --format=xml > ekstrenka/InitData/ResultAction.xml

set +x