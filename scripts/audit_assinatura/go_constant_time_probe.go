// PROBE Go: subtle.ConstantTimeCompare com comprimentos diferentes.
// Go é o caso BOM: não lança, retorna 0 (nunca igual) e revela só o
// comprimento (que não depende do conteúdo) => sem DoS, sem vazamento útil.
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"fmt"
)

func main() {
	segredo := []byte("whsec_exemplo")
	corpo := []byte(`{"event":"billing.paid"}`)
	m := hmac.New(sha256.New, segredo)
	m.Write(corpo)
	digest := hex.EncodeToString(m.Sum(nil))

	fmt.Println("--- subtle.ConstantTimeCompare (Go) ---")
	casos := []struct {
		rotulo string
		a, b   string
	}{
		{"iguais", digest, digest},
		{"vazio vs digest (atacante não manda header)", "", digest},
		{"prefixo de 8 chars", digest[:8], digest},
		{"digest vs digest (bytea)", digest, digest + "\x00"},
		{"case diferente (hex maiúsculo)", fmt.Sprintf("%X", mustHex(digest)), digest},
	}
	for _, c := range casos {
		// mesma ordem que o código de produção costuma usar
		r := subtle.ConstantTimeCompare([]byte(c.a), []byte(c.b))
		fmt.Printf("  %-46s -> %d\n", c.rotulo, r)
	}
	fmt.Println("\n  Regra: Go devolve 0 (seguro) quando o comprimento difere.")
	fmt.Println("  Compare com Node/Python, que LANÇAM exceção no mesmo caso.")
}

func mustHex(s string) []byte {
	b, _ := hex.DecodeString(s)
	return b
}
