<script setup lang="ts">
  // 홈 뷰에 필요한 상태(data)나 메서드(methods)가 있다면 여기에 정의합니다.
  // 현재는 정적 페이지 구성이므로 비워둡니다.

  import { ref, onMounted } from 'vue' // ref와 onMounted 훅 임포트
  import { useRouter } from 'vue-router'

  const router = useRouter()

  // 'AI' 상담 시작하기 버튼 클릭 핸들러
  const startAiConsult = () => {
    // /ai 경로로 이동합니다.
    router.push('/ai')
  }

  // 공고 둘러보기 버튼 클릭 핸들러
  const viewNotices = () => {
    // /list 경로로 이동합니다.
    router.push('/list')
  }

  interface DashBoardInfo {  
    CNT_ALL: number;
    CNT_NOTE_ING: number;
    CNT_APP_ING: number;
    CNT_ELSE: number;
  }

  // API 결과를 저장할 반응형 변수. 초기값은 빈 객체 또는 기본값으로 설정
  const dashboardData = ref<DashBoardInfo>({
    CNT_ALL: 0,
    CNT_NOTE_ING: 0,
    CNT_APP_ING: 0,
    CNT_ELSE: 0,
  });

  const getDashBoard = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/stats', {
          method: 'GET',
          headers: {
              'Content-Type': 'application/json',
          }
      });

      if (!response.ok) {
          throw new Error(`HTTP 오류! 상태 코드: ${response.status}`);
      }

      const return_value: DashBoardInfo = await response.json();
      
      // 💡 API 결과를 반응형 변수(.value)에 할당하여 View 업데이트
      dashboardData.value = return_value;

      console.log('대시보드 데이터 로드 성공:', dashboardData.value);

    } catch (error) {
      console.error('API 호출 오류:', error);
    }
  }

// 💡 컴포넌트가 마운트된 후 데이터 로드 함수 호출
onMounted(() => {
    getDashBoard()
});


// 첨부된 HTML 파일에 있던 간단한 JavaScript 함수는 Vue 방식으로 처리하는 것이 좋습니다.
// function toggleClassName(element, event) { ... } 와 같은 함수는 더 이상 필요 없습니다.
</script>

<template>
  <header class="com-header-wrap">
    <div class="ui-breadcrumb">
      <ul class="location">
        <li>
          <strong class="sb">홈</strong>
        </li>
      </ul>
      <div class="info">
        <small>LH · SH · GH 공식 정보 기반</small>
      </div>
    </div>
  </header>
  <main class="layout-contents bgc-pageBg shadow">
    <div class="inner">
      <div>
        <section class="section1">
          <div class="card">
            <div>
              <i class="ui-badge deep">AI 기반 공공주택 정보 플랫폼</i>
            </div>

            <div class="title">
              <span class="txt-gray500">LH, SH, GH</span>의 실제 공고
              문서를 <strong class="txt-blue600">AI</strong>가 분석하여
              정확하고,
              <br />
              <strong class="txt-green500">
                "명확한 답변을 제공합니다!"
              </strong>
            </div>

            <div class="btns">
              <button class="ui-btn fill primary" @click="startAiConsult">
                <strong class="b">'AI'</strong> 상담 시작하기
              </button>
              <button class="ui-btn outlined" @click="viewNotices">
                공고 둘러보기
              </button>
            </div>
          </div>

          <div class="card">
            <div class="icon-has-txt">
              <i class="fa-solid fa-robot txt-violet400"></i>
              <div class="txt">
                <div class="tit">
                  <strong class="txt-blue600">AI</strong> 기반 분석
                </div>
                <div class="desc">실시간 공고 분석</div>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="icon-has-txt">
              <i class="fa-solid fa-circle-info txt-blue400"></i>
              <div class="txt">
                <div class="tit">정확한 정보</div>
                <div class="desc">LH · SH · GH 공식문서</div>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="icon-has-txt">
              <i class="fa-solid fa-gear txt-orange400"></i>
              <div class="txt">
                <div class="tit">맞춤형 추천</div>
                <div class="desc">개인별 최적화</div>
              </div>
            </div>
          </div>
        </section>

        <section class="section2">
          <div class="card outlined">
            <div class="icon-has-txt">
              <div class="txt">
                <div class="tit">{{ dashboardData.CNT_ALL }}</div>
                <div class="desc">전체 공고 수</div>
              </div>
            </div>
          </div>
          <div class="card outlined">
            <div class="icon-has-txt">
              <div class="txt">
                <div class="tit">{{ dashboardData.CNT_NOTE_ING }}</div>
                <div class="desc">접수 예정 공고</div>
              </div>
            </div>
          </div>
          <div class="card outlined">
            <div class="icon-has-txt">
              <div class="txt">
                <div class="tit">{{ dashboardData.CNT_APP_ING }}</div>
                <div class="desc">접수 중인 공고</div>
              </div>
            </div>
          </div>
          <div class="card outlined">
            <div class="icon-has-txt">
              <div class="txt">
                <div class="tit">{{ dashboardData.CNT_ELSE }}</div>
                <div class="desc">기타 공고</div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </main>
  </template>

<style scoped>
/* HomeView.vue에만 적용될 스타일이 있다면 여기에 작성합니다. */
/* 현재는 원본 HTML에 연결된 style.css 파일을 전역적으로 사용한다고 가정합니다. */
</style>