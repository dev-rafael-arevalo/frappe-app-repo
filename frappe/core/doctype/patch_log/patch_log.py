# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.model.document import Document


class PatchLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		patch: DF.Code | None
		skipped: DF.Check
		traceback: DF.Code | None
	# end: auto-generated types
	@frappe.whitelist()
	def rerun_patch(self):
		from frappe.modules.patch_handler import run_single

		if not frappe.conf.developer_mode:
			frappe.throw(_("Re-running patch is only allowed in developer mode."))

		run_single(self.patch, force=True)
		frappe.msgprint(_("Successfully re-ran patch: {0}").format(self.patch), alert=True)


def before_migrate():
	frappe.reload_doc("core", "doctype", "patch_log")
