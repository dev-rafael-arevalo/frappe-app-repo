# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import unittest
import frappe
from frappe.desk.search import search_link
from frappe.desk.search import search_widget

class TestSearch(unittest.TestCase):
	def setUp(self):
		self.tree_doctype_name = 'Test Tree Order'

		# Create Tree doctype
		self.tree_doc = frappe.get_doc({
			'doctype': 'DocType',
			'name': self.tree_doctype_name,
			'module': 'Custom',
			'custom': 1,
			'is_tree': 1,
			'autoname': 'field:random',
			'fields': [{
				'fieldname': 'random',
				'label': 'Random',
				'fieldtype': 'Data'
			}]
		}).insert()
		self.tree_doc.search_fields = 'parent_test_tree_order'
		self.tree_doc.save()

		# Create root for the tree doctype
		self.parent_doctype_name = 'All Territories'
		frappe.get_doc(doctype=self.tree_doctype_name, random=self.parent_doctype_name,
						is_group=1).insert()

		# Create children for the root
		self.child_doctypes_names = ['USA', 'India', 'Russia', 'China']
		self.child_doctype_list = []
		for child_name in self.child_doctypes_names:
			temp = frappe.get_doc(doctype=self.tree_doctype_name, random=child_name,
								parent_test_tree_order=self.parent_doctype_name)
			temp.insert()
			self.child_doctype_list.append(temp)

	def tearDown(self):
		# Deleting all the created doctype
		for child_doctype in self.child_doctype_list:
			child_doctype.delete()
		frappe.delete_doc(self.tree_doctype_name, self.parent_doctype_name,
						force=1, ignore_permissions=True, for_reload=True)
		self.tree_doc.delete()

	def test_search_field_sanitizer(self):
		# pass
		search_link('DocType', 'User', query=None, filters=None, page_length=20, searchfield='name')
		result = frappe.response['results'][0]
		self.assertTrue('User' in result['value'])

		#raise exception on injection
		self.assertRaises(frappe.DataError,
			search_link, 'DocType', 'Customer', query=None, filters=None,
			page_length=20, searchfield='1=1')

		self.assertRaises(frappe.DataError,
			search_link, 'DocType', 'Customer', query=None, filters=None,
			page_length=20, searchfield='select * from tabSessions) --')

		self.assertRaises(frappe.DataError,
			search_link, 'DocType', 'Customer', query=None, filters=None,
			page_length=20, searchfield='name or (select * from tabSessions)')

		self.assertRaises(frappe.DataError,
			search_link, 'DocType', 'Customer', query=None, filters=None,
			page_length=20, searchfield='*')

		self.assertRaises(frappe.DataError,
			search_link, 'DocType', 'Customer', query=None, filters=None,
			page_length=20, searchfield=';')

		self.assertRaises(frappe.DataError,
			search_link, 'DocType', 'Customer', query=None, filters=None,
			page_length=20, searchfield=';')

	def test_link_field_order(self):
		# Making a request to the search_link with the tree doctype
		search_link(doctype=self.tree_doctype_name, txt='all', query=None,
					filters=None, page_length=20, searchfield=None)
		result = frappe.response['results']

		# Check whether the result is sorted or not
		self.assertEquals(self.parent_doctype_name, result[0]['value'])

		# Check whether searching for parent also list out children
		self.assertEquals(len(result), len(self.child_doctypes_names) + 1)

	#Search for the word "pay", part of the word "pays" (country) in french.
	def test_link_search_in_foreign_language(self):
		try:
			frappe.local.lang = 'fr'
			search_widget(doctype="DocType", txt="pay", page_length=20)
			output = frappe.response["values"]

			result = [['found' for x in y if x=="Country"] for y in output]
			self.assertTrue(['found'] in result)
		finally:
			frappe.local.lang = 'en'

	def test_validate_and_sanitize_search_inputs(self):

		# should raise error if searchfield is injectable
		self.assertRaises(frappe.DataError,
			get_data, *('User', 'Random', 'select * from tabSessions) --', '1', '10', dict()))

		# page_len and start should be converted to int
		self.assertListEqual(get_data('User', 'Random', 'email', 'name or (select * from tabSessions)', '10', dict()),
			['User', 'Random', 'email', 0, 10, {}])
		self.assertListEqual(get_data('User', 'Random', 'email', page_len='2', start='10', filters=dict()),
			['User', 'Random', 'email', 10, 2, {}])

		# DocType can be passed as None which should be accepted
		self.assertListEqual(get_data(None, 'Random', 'email', '2', '10', dict()),
			[None, 'Random', 'email', 2, 10, {}])

		# return empty string if passed doctype is invalid
		self.assertListEqual(get_data("Random DocType", 'Random', 'email', '2', '10', dict()), [])

		# should not fail if function is called via frappe.call with extra arguments
		args = ("Random DocType", 'Random', 'email', '2', '10', dict())
		kwargs = {'as_dict': False}
		self.assertListEqual(frappe.call('frappe.tests.test_search.get_data', *args, **kwargs), [])

		# should not fail if query has @ symbol in it
		search_link('User', 'user@random', searchfield='name')
		self.assertListEqual(frappe.response['results'], [])

@frappe.validate_and_sanitize_search_inputs
def get_data(doctype, txt, searchfield, start, page_len, filters):
	return [doctype, txt, searchfield, start, page_len, filters]
