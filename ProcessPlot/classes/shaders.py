



BasicFragShader ='''#version 150
    in vec4 color;
    out vec4 fColor;

    void main () {
      fColor = color;
    }'''

BasicVertShader='''#version  150
in vec2 vert;
in vec4 in_color;
out vec4 color;
void main () {
  color = in_color;
  gl_Position = vec4(vert, -.99f, 1.0f);
}'''

PenVertShader='''#version  150
in float time;
in float value;
in vec4 scale;
in vec4 in_color;
out vec4 color;
float scale_vals (in float in_val, in float in_min, in float in_max){
    float val = 0.0;
    if (in_max != in_min){
    val = float (((in_val - in_min) / (in_max - in_min)) - 0.5); //scale to gl -0.5 , 0.5
    }
  return(val);
}
void main () {
  color = in_color;
  gl_Position = vec4(scale_vals(time, scale[0], scale[1]),
                       scale_vals(value, scale[2], scale[3]), 0.0, 1.0);
}'''