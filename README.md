사진 포함 설명 :

https://y-y-y-y.tistory.com/16


----


https://prod.danawa.com/list/?cate=102110

다나와 냉장고 페이지를 들어가보면

 

메인에 냉장:147L/냉동:101L 이런 식으로 사양이 써져 있는 제품들이 많다.
 


 

코멧 브라우저로도 할 수 있지만, 시간이 너무나도 오래 걸린다. 특히 오히려 이런 작업에 한계가 있다.

 

 

이것을 파이썬으로 크롤링 '딸깍' 해서 데이터를 받아올 수 있다.

 

1. danawa_fridge_crawl.py 파일을 받는다.

 

2. pip install selenium bs4 chromedriver-autoinstaller

를 설치하고

 

3. 위 파이썬을 실행한다.

 

끝이다!

 

결과물은

danawa_fridge_capacity.csv

에 저장된다.

 


 

처음에 저 다음 페이지 버튼을 못찾길래 F12로 페이지 요소를 찾아서 알려주니 제대로 코드를 짤 수 있었다.

 

조금만 응용하면 이것 뿐 아니라 유사한 작업에는 다 쓸 수 있을 것이다.

 ---

 https://github.com/heelee912/danawa_crawl/issues # 게시판
