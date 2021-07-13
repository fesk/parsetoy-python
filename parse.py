#!/usr/bin/python3
"""
//- Copyright (c) 2021, Nick Besant hwf@fesk.net. All rights reserved.
//- licenced under GPLv3, see LICENCE.txt

parse.py - *toy* parser and examples for simple boolean-like statements such as;
    "conditionA and conditionB"
    "conditionA and (conditionB or conditionC)"
    "conditionA and (conditionB or (conditionC and conditionD))"
    "conditionA and not (conditionB or (conditionC and conditionD))"

    Built-in evaluate() allows "conditionX" to only be "x<y" or "x>y" where x and y are ints.
    Another example evaluate() in CustomParse is given where "conditionX" is in the
    form "key.attr=str".

    This is intended to be used to allow you to specify your own condition grammar to test the
    truthiness of a statement, e.g. "field1.contains{x} or field2.contains{y}".

    Use of parentheses () is only allowed for grouping conditions, they can't appear anywhere else
    in the condition.  If you need them in your statements, you could add them with an escape
    character and modify the code to support that.

    There is minimal error checking / verification (intentionally), this is not meant for
    production use.

"""
import logging
import sys


class Parse:
    """Simple parser for statements like: "condition1 or condition2 and (condition3 or condition4)"
     Supports nested parentheses.

     Default evaluate() method only supports "condition" to be "x<y" or "x>y" where x and y are ints.
     Override evaluate() to test your condition syntax against class .data attribute (or anything
     else you want).
     """

    dry_run = False
    logger = None
    data = None

    def __init__(self, data=None, dry_run=False, log_level=logging.ERROR, logger=None):
        """
        :param data: (object) - the data you want to evaluate against in self.evaluate
        :param dry_run: (bool) don't do any actual evaluation, just parsing/simplification
        :param log_level: (int) log level.  Use logging.DEBUG -> logging.ERROR (default).
        :param log_to: (None|object) logging.getLogger instance or None, if None then log to stdout.
        """
        self.dry_run = dry_run
        self.data = data
        if type(log_level) == int and log_level >= 0:
            self.log_level = log_level
        else:
            print("\n!!\tinit: log_level {0} not valid, ignoring it".format(log_level))
        if logger is not None:
            if not hasattr(logger, 'debug'):
                print("\n!!\tinit: logger {0} not a valid logging.getLogger, using stdout".format(logger))
            else:
                self.logger = logger

    def log(self, level, msg):
        if self.log_level <= level:
            if self.logger is None:
                print(msg)
            else:
                self.logger.log(level, msg.replace('\n', ' '))

    def parse(self, expr):
        """Parse expr: use for checking syntax."""
        self.raw_expr = expr
        self.expr = expr

        # condition and (condition or (condition and condition))

        # equivalent to;
        # TRUE|FALSE and (TRUE|FALSE or (TRUE|FALSE and TRUE|FALSE))

        # evaluate everything in brackets;
        # (TRUE|FALSE or (TRUE|FALSE and TRUE|FALSE))
        # evaluate first:     (TRUE|FALSE and TRUE|FALSE)
        #       becomes TRUE|FALSE, so outer expression becomes;
        # (TRUE|FALSE or TRUE|FALSE), which evaluates to;
        # TRUE|FALSE

        self.log(logging.DEBUG, 'INPUT expression:\n{0}'.format(self.expr))
        self.simplify_parens(self.expr, 0)
        self.log(logging.DEBUG, '\nINPUT:\n{0}\nSIMPLIFIED to:\n{1}'.format(self.raw_expr, self.expr))
        return self.test(self.eval_section(self.expr))

    def check_match(self, expr, data):
        self.data = data
        self.expr = expr
        self.simplify_parens(self.expr, 0)
        return self.test(self.eval_section(self.expr))

    def simplify_parens(self, expr, nesting=0):
        if '(' not in expr:
            return

        this_eval = expr

        current_expr = ''

        in_paren = False

        section_index = 0

        for c in this_eval:
            if in_paren:
                if c == ')':
                    in_paren = False
                    self.log(logging.DEBUG, '{0}: section: {1}'.format(nesting, current_expr))
                    if '(' in current_expr:
                        current_expr += c
                        # there are more nested parens in this section
                        self.simplify_parens(current_expr, nesting+1)
                    else:
                        # current stack is for evaluation
                        self.log(logging.DEBUG, '{0}: EVAL {1}'.format(nesting, current_expr))
                        paren_result = self.eval_section(current_expr)
                        self.log(logging.DEBUG, '{0}: section result: {1}'.format(nesting, paren_result))
                        self.expr = self.expr.replace('(' + current_expr + ')', paren_result)
                        self.log(logging.DEBUG, '{0}: current expr: {1}'.format(nesting, self.expr))
                        if '(' in self.expr:
                            self.simplify_parens(self.expr, nesting + 1)
                else:
                    current_expr += c
            else:
                if c == '(':
                    self.log(logging.DEBUG, '\tNew parentheses section')
                    current_expr = ''
                    in_paren = True

            section_index += 1

            continue

    def eval_section(self, section):

        # parse LTR "condition"
        # optional AND / OR / NOT and then more "condition"
        #
        section = section.replace(' AND ', ' and ').replace(' OR ', ' or ').replace(' NOT ', ' not ')
        # AND conditions first, all must eval to true
        and_parts = section.split(' and ')
        self.log(logging.DEBUG, '\tAND sections: {0}'.format(and_parts))
        true_parts = 0
        for part in and_parts:
            if ' or ' in part:
                # This section is TRUE if ANY of the OR parts are TRUE
                for or_part in part.split(' or '):
                    if self.test(or_part):
                        true_parts += 1
                        self.log(logging.DEBUG, '\tOR section "{0}" is TRUE'.format(part))
                        break

            else:
                # This section is TRUE if this part is TRUE
                if self.test(part):
                    self.log(logging.DEBUG, '\tAND section "{0}" is TRUE'.format(part))
                    true_parts += 1
                else:
                    self.log(logging.DEBUG, '\tAND section "{0}" is FALSE'.format(part))

        if true_parts == len(and_parts):
            # All TRUE, so return as TRUE
            return '__TRUE__'
        else:
            return '__FALSE__'

    def test(self, s):
        """Test if a section (with/without NOT) is True"""
        if s == '__TRUE__':
            return True
        elif s == '__FALSE__':
            return False
        else:
            if s.startswith('not '):
                must_negate = True
                s = s.lstrip('not ').strip()
            else:
                must_negate = False
                s = s.strip()

            if self.dry_run:
                return True
            else:
                eval_result = self.evaluate(s)
                if must_negate:
                    return True if eval_result is False else False
                else:
                    return eval_result

    def evaluate(self, condition):
        """
        Stub: override this to test "condition" against self.data.  This stub method
        is for reference and supports "condition" as only;
            x>y or x<y where x and y are ints.

        :param condition: (str) condition to test against self.data
        :return: (bool)
        """

        if '<' in condition:
            parts = condition.split('<')
            if len(parts) != 2:
                raise ValueError('Condition "{0}" is not x<y'.format(condition))
            try:
                return int(parts[0]) < int(parts[1])
            except:
                raise ValueError('Condition "{0}" is not (int)<(int)'.format(condition))
        elif '>' in condition:
            parts = condition.split('>')
            if len(parts) != 2:
                raise ValueError('Condition "{0}" is not x>y'.format(condition))
            try:
                return int(parts[0]) > int(parts[1])
            except:
                raise ValueError('Condition "{0}" is not (int)>(int)'.format(condition))
        else:
            raise ValueError('Condition "{0}" is not x>y or x<y'.format(condition))


class CustomParse(Parse):
    """Example evaluate section.  Condition for evaluate() is expected to be
    userX.attr=str based on self.data set in evaluate()"""
    def evaluate(self, condition):
        """Example - alternate evaluate()"""
        self.data = {'user1': {'name': 'alice', 'height': 1.8},
                     'user2': {'name': 'bob', 'height': 1.65},
                     }

        if '.' not in condition:
            raise ValueError("{0} invalid".format(condition))

        cond_parts = condition.split('.')
        if cond_parts[0] in self.data.keys():
            user = self.data[cond_parts[0]]
            attr, test = cond_parts[1].split('=')
            if attr in user.keys():
                return user[attr] == test
            else:
                raise ValueError("attr {0} in {1} not recognised".format(cond_parts[attr], condition))
        else:
            raise ValueError("{0} in {1} not recognised".format(cond_parts[0], condition))


def main():
    if len(sys.argv) > 1:
        p = CustomParse(log_level=logging.DEBUG)
        print(p.check_match(sys.argv[1], ""))
    else:
        p = Parse(log_level=logging.DEBUG)
        print(p.check_match("1<2 and (1<2 and (3>4 or 6<7)) or (0<1 and 10>10)", ""))


if __name__ == '__main__':
    main()
