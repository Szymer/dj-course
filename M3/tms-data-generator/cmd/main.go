package main

import (
	"fmt"
	"os"

	"tms-data-generator/generator"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: generator <output_file>")
		os.Exit(1)
	}
	outputFile := os.Args[1]
	if err := generator.Generate(outputFile); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
