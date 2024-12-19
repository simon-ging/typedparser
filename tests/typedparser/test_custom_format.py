import argparse
from typedparser.custom_format import CustomArgparseFmt

def test_custom_argparse_fmt():
    parser = argparse.ArgumentParser(formatter_class=CustomArgparseFmt)
    parser.add_argument('--test', type=str, default='default', help='Test argument')
    
    help_output = parser.format_help()
    assert '--test' in help_output
    assert 'default' in help_output
    assert 'Test argument' in help_output
