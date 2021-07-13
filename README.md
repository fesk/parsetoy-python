# parsetoy-python

Toy parser implementation with some basic examples, for simple boolean-like statements such as;
```    
  "conditionA and conditionB"
  "conditionA and (conditionB or conditionC)"
  "conditionA and (conditionB or (conditionC and conditionD))"
  "conditionA and not (conditionB or (conditionC and conditionD))"
```  

Built-in **evaluate()** allows *conditionX* to only be **x<y** or **x>y** where *x* and *y* are ints. Another example **evaluate()** in **CustomParse** is given where *conditionX* is in the form **key.attr=str**.

This is intended to be used to allow you to specify your own condition grammar to test the truthiness of a statement, e.g. **field1.contains{x} or field2.contains{y}**.

# Limitations

Use of parentheses () is only allowed for grouping conditions, they can't appear anywhere else in the condition.  If you need them in your statements, you could add them with an escape character and modify the code to support that.

There is minimal error checking / verification (intentionally), this is not meant for production use.

# Usage
```
import parse

class MyParser(parse.Parse):
    def evaluate(self, condition):
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
                     
p = MyParser()
data = {
  'user1': {'name': 'alice', 'height': '1.8'},
  'user2': {'name': 'bob', 'height': '1.65'},
}
print(p.check_match("user1.name=alice or (user2.name=bob and user1.height=1.8)", data))

```


# Quick demo
```$ python3 parse.py```
Uses built-in demo condition check to test truthiness of **1<2 and (1<2 and (3>4 or 6<7)) or (0<1 and 10>10)**.  Lots of debug output.

```$ python3 parse.py "user1.name=alice or user2.name=bob"```
Uses "CustomParser" example demo condition check to test truthiness of **user1.name=alice or user2.name=bob**.  Lots of debug output.

