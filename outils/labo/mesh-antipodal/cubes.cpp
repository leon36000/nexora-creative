#include <antipodal/gwn_mesh.hh>
#include <antipodal/intersector/intersector.hh>
#include <array>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <numbers>
#include <span>
#include <string_view>
#include <vector>

// Independent signed solid-angle summation, not the antipodal decomposition.
struct V { double x,y,z; };
V sub(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
double dot3(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
V cross3(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
double norm3(V a){return std::sqrt(dot3(a,a));}
double solid_angle_winding(std::span<antipodal::vec3<double> const> vertices,std::span<int const> indices,V p){
 double sum=0;
 for(size_t i=0;i<indices.size();i+=3){
  auto v0=vertices[indices[i]],v1=vertices[indices[i+1]],v2=vertices[indices[i+2]];
  V a=sub({v0.x,v0.y,v0.z},p),b=sub({v1.x,v1.y,v1.z},p),c=sub({v2.x,v2.y,v2.z},p);
  double la=norm3(a),lb=norm3(b),lc=norm3(c);
  double det=dot3(a,cross3(b,c));
  double denom=la*lb*lc+dot3(a,b)*lc+dot3(b,c)*la+dot3(c,a)*lb;
  sum+=2*std::atan2(det,denom);
 }
 return sum/(4*std::numbers::pi);
}
int main(){
 using namespace antipodal;using T=double;
 const std::vector<vec3<T>> verts={{-.5,-.5,-.5},{.5,-.5,-.5},{-.5,.5,-.5},{.5,.5,-.5},{-.5,-.5,.5},{.5,-.5,.5},{-.5,.5,.5},{.5,.5,.5}};
 const std::vector<int> closed={0,2,1,1,2,3,4,5,6,6,5,7,0,4,2,2,4,6,1,3,5,5,3,7,0,1,4,4,1,5,2,6,3,3,6,7};
 auto open=closed;open.resize(30);auto flipped=closed;std::swap(flipped[1],flipped[2]);auto reversed=closed;for(size_t i=0;i<reversed.size();i+=3)std::swap(reversed[i+1],reversed[i+2]);
 const std::array<V,5> points={V{0,0,0},V{.1,-.2,.3},V{.49,.01,.02},V{2,0,0},V{0,1.5,0}};
 const std::array<vec3<T>,2> dirs={normalize(vec3<T>{.31,.57,.76}),normalize(vec3<T>{.23,-.71,.66})};
 std::cout<<std::setprecision(17);int failures=0;double largest=0;unsigned checks=0;
 for(auto [label,ids]:std::array<std::pair<std::string_view,std::vector<int> const*>,4>{{{"closed",&closed},{"open",&open},{"flipped",&flipped},{"reversed",&reversed}}}){
  NaiveIntersector<T> isect{verts,*ids};const auto boundary=build_boundary_segments<T>(verts,*ids);
  std::cout<<"case="<<label<<" triangles="<<ids->size()/3<<" boundary_segments="<<boundary.size()<<'\n';
  for(size_t i=0;i<points.size();i++){
   auto p=points[i];double ref=solid_angle_winding(verts,*ids,p);std::cout<<" point="<<i<<" direct="<<ref;
   for(auto direction:dirs){double got=eval_gwnr_mesh_single<NaiveIntersector<T>,T>({p.x,p.y,p.z},direction,boundary,isect);double delta=std::abs(got-ref);largest=std::max(largest,delta);checks++;if(!std::isfinite(got)||delta>1e-9)failures++;std::cout<<" antipodal="<<got<<" error="<<delta;}
   std::cout<<'\n';
  }
  double center=solid_angle_winding(verts,*ids,points[0]);
  double expected=label=="closed"?1.0:(label=="reversed"?-1.0:5.0/6.0);if(std::abs(center-expected)>1e-12)failures++;
 }
 std::cout<<"checks="<<checks<<" max_abs_error="<<largest<<" failures="<<failures<<'\n';return failures?1:0;
}
