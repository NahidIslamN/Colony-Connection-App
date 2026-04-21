from importlib import import_module

_terms_condition = import_module("apps.admin_dashboard.models.terms_condition")


TermsCondition = _terms_condition.TermsCondition


__all__ = [    
	"TermsCondition"
]