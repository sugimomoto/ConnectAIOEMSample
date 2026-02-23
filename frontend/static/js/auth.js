const apiClient = new APIClient();

async function logout() {
  try {
    await apiClient.logout();
    window.location.href = '/login';
  } catch (e) {
    console.error('ログアウトに失敗しました', e);
  }
}
