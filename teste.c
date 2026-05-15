#include <stdio.h>

int main() {
  int n=50, o;

  

  do
  {
    printf("Digite o valor da aposta: ");
    scanf("%d", &o);

    if(o==n) {
      printf("Parabéns, você acertou o número!\n");
    } else if (o > n) {
      printf("O número é menor que %d. Tente novamente.\n", o);
    } else {
      printf("O número é maior que %d. Tente novamente.\n", o);
    }
  } while (o != n);

  
  return 0;
}