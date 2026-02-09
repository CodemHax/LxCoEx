from typing import Dict

CODE_TEMPLATES: Dict[str, str] = {
    "python": '''def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
print("Happy coding!")
''',

    "javascript": '''function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet("World"));
console.log("Happy coding!");
''',

    "go": '''package main

import "fmt"

func greet(name string) string {
    return fmt.Sprintf("Hello, %s!", name)
}

func main() {
    fmt.Println(greet("World"))
    fmt.Println("Happy coding!")
}
''',

    "java": '''public class Main {
    public static String greet(String name) {
        return "Hello, " + name + "!";
    }

    public static void main(String[] args) {
        System.out.println(greet("World"));
        System.out.println("Happy coding!");
    }
}
''',

    "c": '''#include <stdio.h>

void greet(const char* name) {
    printf("Hello, %s!\\n", name);
}

int main() {
    greet("World");
    printf("Happy coding!\\n");
    return 0;
}
''',

    "cpp": '''#include <iostream>
#include <string>

std::string greet(const std::string& name) {
    return "Hello, " + name + "!";
}

int main() {
    std::cout << greet("World") << std::endl;
    std::cout << "Happy coding!" << std::endl;
    return 0;
}
''',

    "typescript": '''function greet(name: string): string {
    return `Hello, ${name}!`;
}

console.log(greet("World"));
console.log("Happy coding!");
'''
}


def get_template(language: str) -> str:
    language = language.lower().strip()
    return CODE_TEMPLATES.get(language, CODE_TEMPLATES.get("python", ""))


def get_all_templates() -> Dict[str, str]:
    return CODE_TEMPLATES


def get_available_languages() -> list:
    return list(CODE_TEMPLATES.keys())
