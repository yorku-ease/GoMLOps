'''
Note: below code is 100 percent trial and error. I have no idea how 
ast is actually supposed to be used. I brute forced this one with the 
dir() function and a lot of patience.
Proceed with caution. 
The basic idea is to 
	a. find the index of the Argparse.ArgumentParser assignment in the code
	b. find the index of the parse_args() call 
	c. Get the name of the instance variable to which ArgumentParser was assigned
	d. Use that knowledge to extract all of the add_argument calls inbetween the 
		 index of the contructor, and the index of the parse_args() call. 
We'll see how robust this turns out to be.
'''
import os 
import ast 
import random
from itertools import chain
from ast import  NodeVisitor

class FindCall(NodeVisitor):
	def __init__(self, *args):
		if len(args) < 1:
			raise ValueError("At least one target function must be specified")
		self.result = {arg: [] for arg in args}

	def visit_Call(self, node):
		if hasattr(node.func, "id"):
			if node.func.id in self.result:
				self.result[node.func.id].append(node)
		elif hasattr(node.func, "attr"):
			if node.func.attr in self.result:
				self.result[node.func.attr].append(node)
		# visit the children
		self.generic_visit(node)

class ParserError(Exception):
	'''Thrown when the parser can't find argparse functions the client code'''
	pass

def get_files(project, ext=".py"):
	filenames = []
	for root, _, files in os.walk(project):
		for file in files:
			if file.endswith(ext):
				filenames.append(os.path.join(root, file))
	return filenames

def get_argparse(file_name):
	calls = FindCall("ArgumentParser", "add_argument")

	content = open(os.path.abspath(file_name)).read()
	body = ast.parse(content)

	calls.visit(body)
	try:
		argparse_assign_obj = calls.result['ArgumentParser'][0]
		nodes = calls.result["add_argument"]
		parser_var_name = nodes[0].func.value.id
		ast_source = chain([argparse_assign_obj], nodes)
		
		code = []
		# convert ast to python code
		for ast_s in ast_source:
			code.append(ast.get_source_segment(content, ast_s))
		#code = list(map(ast.get_source_segment, ast_source))
		# Add line of code which stores the argparse values
		code.append('INFO = {}._actions'.format(parser_var_name))
		code.append('parser = {}'.format(parser_var_name))

		return code, parser_var_name
	except IndexError:
		return None, None

def make_random_filename(length):
	filename = os.path.join(os.path.dirname(__file__), 'tmp_' + ''.join([str(random.randint(0,10)) for _ in range(length)]) + '.py')
	# Make sure it doesn't inadvertently write over a 
	# file (as slim of a chance as that may be)
	while os.path.exists(os.path.join(os.path.dirname(__file__), filename)):
		make_random_filename()
	return filename

def load_module(module):
		return __import__(module)

def save_to_module(parser_var_name, code, tmp_file):
	'''
	Saves the argparse code to a temporary file
	'''
	try: 
		with open(tmp_file, 'w') as f:
			f.write('import argparse\n')
			f.write('from argparse import ArgumentParser\n')
			for line in code: 
				if line.startswith('ArgumentParser') or line.startswith('argparse'):
					f.write(f'{parser_var_name} = {line}' + '\n')
				else:
					f.write(f'{line}' + '\n')
	except IOError:
		raise IOError('Could not save temporary file')

def delete_module(tmp_file):
	"Deletes the temporary files"
	try: 
		os.remove(tmp_file)
		if os.path.exists(tmp_file.replace('.py', '.pyc')):
			os.remove(tmp_file.replace('.py', '.pyc'))
	except Exception as e:
		print('WARNING: Failed to delete temporary file {}.'.format(tmp_file), e)

def get_args(arg_info):
	args = []
	for attribs in arg_info:
		if not '-h' in vars(attribs)['option_strings']:
			arg = {
					"option_strings": vars(attribs)['option_strings'],
					"input": False if vars(attribs)['nargs'] == 0 else True ,
					"destination": vars(attribs)['dest'] if vars(attribs)['dest'] else None,
					"default": vars(attribs)['default'],
					"type": "float" if vars(attribs)['default'].__class__.__name__ in ["int", "float"]  else "str",
					"required": vars(attribs)['required'],
					"choices": vars(attribs)['choices'],
					"help": vars(attribs)['help']
				}
			if arg not in args:
				args.append(arg)
	return args