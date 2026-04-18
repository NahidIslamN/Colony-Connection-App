from importlib import import_module

_subscribplan = import_module("apps.managements.models.subscribplan")
_managements = import_module("apps.managements.models.managements")

SubscribePlan = _subscribplan.SubscribePlan
Company = _managements.Company
SalesRepresentative = _managements.SalesRepresentative
Customer = _managements.Customer
Colony = _managements.Colony
VisitColony = _managements.VisitColony
CustomerNote = _managements.CustomerNote
CustomerMechanary = _managements.CustomerMechanary

__all__ = [
	"SubscribePlan",
	"Company",
	"SalesRepresentative",
	"Customer",
	"Colony",
	"VisitColony",
	"CustomerNote",
	"CustomerMechanary",
]
