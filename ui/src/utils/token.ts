// 检查token是否存在且有效
export const isTokenValid = (): boolean => {
  const token = localStorage.getItem('token')
  if (!token) {
    return false
  }
  
  // 简单检查token格式是否正确
  try {
    const parts = token.split('.')
    if (parts.length !== 3) {
      return false
    }
    
    // 检查token是否过期
    const payload = JSON.parse(atob(parts[1]))
    const exp = payload.exp
    if (exp && Date.now() >= exp * 1000) {
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
      localStorage.removeItem('user')
      return false
    }
    
    return true
  } catch (error) {
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('user')
    return false
  }
}