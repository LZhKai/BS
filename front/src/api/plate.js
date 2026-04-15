import requestPy from './request_py'

export const recognizePlate = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return requestPy({
    url: '/register/recognize',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
}

export const saveRecognizedVehicle = (data) => {
  return requestPy({
    url: '/register/vehicle/save',
    method: 'post',
    data
  })
}

export const getPlateRecords = (params) => {
  return requestPy({
    url: '/register/records',
    method: 'get',
    params
  })
}
