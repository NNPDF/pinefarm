c     cut on Higgs particles
      do i=1,nexternal
        if (ipdg(i) .eq. 25) then
          if (abs(atanh(p(3,i)/p(0,i)))
     &        .gt. {}) then
            passcuts_leptons=.false.
            return
          endif
        endif
      enddo
